"""Integration coverage for Maintenance role and assigned-vehicle access."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_current_user
from app.models.driver import Driver
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.notification import Notification
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle, VehicleStatus
from app.tasks.maintenance import process_maintenance_alerts
from database import Base, get_db
from main import app


class MaintenanceRbacIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False, expire_on_commit=False)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.Session()
            try:
                yield db
            finally:
                db.close()

        def override_current_user():
            return cls.current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_current_user
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.client.close()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.admin = self.make_user("admin", RoleEnum.Admin)
        self.fleet_manager = self.make_user("fleet-manager", RoleEnum.FleetManager)
        self.dispatcher = self.make_user("dispatcher", RoleEnum.Dispatcher)
        self.driver_user = self.make_user("driver", RoleEnum.Driver)
        self.unassigned_driver_user = self.make_user("unassigned-driver", RoleEnum.Driver)
        self.driver = self.make_driver(self.driver_user, "MAINT-DRIVER-1")
        self.make_driver(self.unassigned_driver_user, "MAINT-DRIVER-2")
        self.own_vehicle = self.make_vehicle("OWN", assigned_driver=self.driver.driver_id)
        self.other_vehicle = self.make_vehicle("OTHER")
        type(self).current_user = self.as_current_user(self.admin)

    def db(self):
        return self.Session()

    @staticmethod
    def as_current_user(user):
        return SimpleNamespace(user_id=user.user_id, role=user.role, email=user.email)

    def set_role(self, user):
        type(self).current_user = self.as_current_user(user)

    def make_user(self, label, role):
        db = self.db()
        user = User(full_name=label.title(), email=f"{label}@maintenance-rbac.test", password="hash", phone="9000000000", role=role, email_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        return user

    def make_driver(self, user, license_number):
        db = self.db()
        driver = Driver(user_id=user.user_id, full_name=user.full_name, license_number=license_number)
        db.add(driver)
        db.commit()
        db.refresh(driver)
        db.close()
        return driver

    def make_vehicle(self, suffix, *, assigned_driver=None):
        db = self.db()
        vehicle = Vehicle(registration_number=f"TN88M{suffix}", vehicle_type="Truck", brand="FleetFlow", model="Maintenance", manufacture_year=2024, fuel_type="Diesel", capacity=1000, status=VehicleStatus.Available, assigned_driver=assigned_driver)
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        db.close()
        return vehicle

    def payload(self, vehicle):
        return {"vehicle_id": str(vehicle.vehicle_id), "maintenance_type": "Oil Change", "service_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), "cost": 1500}

    def create_record(self, vehicle):
        response = self.client.post("/maintenance/", json=self.payload(vehicle))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_admin_and_fleet_manager_can_create_update_and_complete(self):
        admin_record = self.create_record(self.own_vehicle)
        started = self.client.put(f"/maintenance/{admin_record['maintenance_id']}", json={"status": "InProgress"})
        self.assertEqual(started.status_code, 200, started.text)
        completed = self.client.put(f"/maintenance/{admin_record['maintenance_id']}", json={"status": "Completed"})
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(completed.json()["status"], "Completed")

        self.set_role(self.fleet_manager)
        manager_record = self.create_record(self.other_vehicle)
        updated = self.client.put(f"/maintenance/{manager_record['maintenance_id']}", json={"remarks": "Fleet Manager review", "status": "Resolved"})
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["status"], "Resolved")

    def test_dispatcher_is_read_only(self):
        record = self.create_record(self.other_vehicle)
        own_record = self.create_record(self.own_vehicle)
        self.set_role(self.dispatcher)
        listed = self.client.get("/maintenance/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(
            {item["maintenance_id"] for item in listed.json()},
            {record["maintenance_id"], own_record["maintenance_id"]},
        )
        self.assertEqual(self.client.get(f"/maintenance/{record['maintenance_id']}").status_code, 200)
        self.assertEqual(self.client.post("/maintenance/", json=self.payload(self.other_vehicle)).status_code, 403)
        self.assertEqual(self.client.put(f"/maintenance/{record['maintenance_id']}", json={"status": "Resolved"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/maintenance/{record['maintenance_id']}").status_code, 403)

    def test_driver_reads_only_assigned_vehicle_and_cannot_manage(self):
        own_record = self.create_record(self.own_vehicle)
        other_record = self.create_record(self.other_vehicle)
        self.set_role(self.driver_user)

        listed = self.client.get("/maintenance/")
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([item["maintenance_id"] for item in listed.json()], [own_record["maintenance_id"]])
        self.assertEqual(self.client.get(f"/maintenance/{own_record['maintenance_id']}").status_code, 200)
        self.assertEqual(self.client.get(f"/maintenance/{other_record['maintenance_id']}").status_code, 403)
        self.assertEqual(self.client.get(f"/maintenance/vehicle/{self.other_vehicle.vehicle_id}").status_code, 403)
        self.assertEqual(self.client.post("/maintenance/", json=self.payload(self.own_vehicle)).status_code, 403)
        self.assertEqual(self.client.put(f"/maintenance/{own_record['maintenance_id']}", json={"status": "Completed"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/maintenance/{own_record['maintenance_id']}").status_code, 403)

    def test_driver_without_assigned_vehicle_receives_empty_list(self):
        self.create_record(self.other_vehicle)
        self.set_role(self.unassigned_driver_user)
        self.assertEqual(self.client.get("/maintenance/").json(), [])

    def test_assigned_driver_receives_only_own_vehicle_maintenance_reminder(self):
        record = self.create_record(self.own_vehicle)
        db = self.db()
        maintenance = db.query(Maintenance).filter(Maintenance.maintenance_id == UUID(record["maintenance_id"])).first()
        now = datetime.now(timezone.utc).replace(microsecond=0)
        maintenance.service_date = now + timedelta(days=5)
        db.commit()

        process_maintenance_alerts(db, now)
        driver_notifications = db.query(Notification).filter(
            Notification.maintenance_id == maintenance.maintenance_id,
            Notification.user_id == self.driver_user.user_id,
        ).all()
        self.assertEqual(len(driver_notifications), 1)
        self.assertEqual(driver_notifications[0].alert_type, "due_in_5_days")
        self.assertEqual(
            db.query(Notification).filter(
                Notification.maintenance_id == maintenance.maintenance_id,
                Notification.user_id == self.unassigned_driver_user.user_id,
            ).count(),
            0,
        )
        db.close()


if __name__ == "__main__":
    unittest.main()
