"""Isolated integration coverage for FleetFlow in-app notifications."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from app.core.deps import get_current_user
from app.crud.shipment import change_shipment_status
from app.models.driver import Driver, DriverStatus
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.notification import Notification
from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip, TripStatus
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle, VehicleStatus
from app.services.notification import create_notification
from app.tasks.maintenance import process_maintenance_alerts


class NotificationIntegrationTests(unittest.TestCase):
    """Notifications use an isolated SQLite database and FastAPI overrides."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
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
        user = User(
            full_name=label.title(), email=f"{label}@notifications.test",
            password="hash", phone="9000000000", role=role, email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        return user

    def make_vehicle(self):
        db = self.db()
        vehicle = Vehicle(
            registration_number="TN99NOTIFY1", vehicle_type="Truck", brand="FleetFlow",
            model="Test", manufacture_year=2025, fuel_type="Diesel", capacity=1000,
            status=VehicleStatus.Available,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        db.close()
        return vehicle

    def make_maintenance(self, vehicle, service_date, status=MaintenanceStatus.Scheduled):
        db = self.db()
        maintenance = Maintenance(
            vehicle_id=vehicle.vehicle_id, maintenance_type="Oil Change", service_date=service_date,
            status=status,
        )
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        db.close()
        return maintenance

    def make_driver(self):
        db = self.db()
        driver = Driver(
            user_id=self.driver_user.user_id, full_name=self.driver_user.full_name,
            license_number="DL-NOTIFY-01", experience_years=3,
            address="Coimbatore", status=DriverStatus.Available,
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        db.close()
        return driver

    def test_service_defaults_and_private_read_api(self):
        db = self.db()
        older = create_notification(
            db, user_id=self.admin.user_id, title="Older", message="Older message",
            notification_type="system", alert_type="test:older",
        )
        newer = create_notification(
            db, user_id=self.admin.user_id, title="Newer", message="Newer message",
            notification_type="system", alert_type="test:newer",
        )
        create_notification(
            db, user_id=self.fleet_manager.user_id, title="Private", message="Hidden",
            notification_type="system", alert_type="test:private",
        )
        self.assertFalse(newer.is_read)
        self.assertIsNotNone(newer.created_at)
        # Make the order deterministic independently of database timestamp precision.
        db.query(Notification).filter(Notification.notification_id == older.notification_id).update(
            {Notification.created_at: datetime.now(timezone.utc) - timedelta(minutes=1)}
        )
        db.commit()
        db.close()

        response = self.client.get("/notifications")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["title"] for item in response.json()], ["Newer", "Older"])

        response = self.client.patch(f"/notifications/{newer.notification_id}/read")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_read"])

        db = self.db()
        foreign_notification = db.query(Notification).filter(Notification.user_id == self.fleet_manager.user_id).first()
        db.close()
        response = self.client.patch(f"/notifications/{foreign_notification.notification_id}/read")
        self.assertEqual(response.status_code, 404)

        response = self.client.patch("/notifications/read-all")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["updated"], 1)
        db = self.db()
        self.assertFalse(db.query(Notification).filter(Notification.notification_id == foreign_notification.notification_id).one().is_read)
        db.close()

    def test_empty_notification_list_is_safe(self):
        response = self.client.get("/notifications")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_maintenance_reminders_deduplicate_and_stop_for_resolved_records(self):
        now = datetime(2026, 8, 27, 8, 0, tzinfo=timezone.utc)
        vehicle = self.make_vehicle()
        due_five = self.make_maintenance(vehicle, now + timedelta(days=5))
        db = self.db()
        result = process_maintenance_alerts(db, now)
        self.assertEqual(result["five_day"], 1)
        self.assertEqual(result["five_day_created"], 1)
        self.assertEqual(db.query(Notification).filter(Notification.maintenance_id == due_five.maintenance_id).count(), 2)
        self.assertEqual(process_maintenance_alerts(db, now)["five_day_created"], 0)

        overdue = self.make_maintenance(vehicle, now - timedelta(days=1))
        self.assertEqual(process_maintenance_alerts(db, now)["overdue_created"], 1)
        self.assertEqual(process_maintenance_alerts(db, now + timedelta(days=1))["overdue_created"], 1)
        overdue.status = MaintenanceStatus.Resolved
        db.merge(overdue)
        db.commit()
        self.assertEqual(process_maintenance_alerts(db, now + timedelta(days=2))["overdue"], 0)
        db.close()

    def test_shipment_transitions_create_one_operational_notification_per_user(self):
        db = self.db()
        shipment = Shipment(
            tracking_number="NOTIFY-001", source="Coimbatore", destination="Chennai",
            customer_name="Customer", shipment_weight=10, status=ShipmentStatus.InTransit,
        )
        db.add(shipment)
        db.commit()
        change_shipment_status(db, shipment, ShipmentStatus.Delivered)
        delivered = db.query(Notification).filter(Notification.alert_type == f"shipment:{shipment.shipment_id}:Delivered").all()
        self.assertEqual(len(delivered), 3)  # Admin, Fleet Manager, Dispatcher.
        change_shipment_status(db, shipment, ShipmentStatus.Delivered)
        self.assertEqual(
            db.query(Notification).filter(Notification.alert_type == f"shipment:{shipment.shipment_id}:Delivered").count(), 3
        )
        delayed = Shipment(
            tracking_number="NOTIFY-002", source="Coimbatore", destination="Chennai",
            customer_name="Customer", shipment_weight=10, status=ShipmentStatus.InTransit,
        )
        cancelled = Shipment(
            tracking_number="NOTIFY-003", source="Coimbatore", destination="Chennai",
            customer_name="Customer", shipment_weight=10, status=ShipmentStatus.Created,
        )
        db.add_all([delayed, cancelled])
        db.commit()
        change_shipment_status(db, delayed, ShipmentStatus.Delayed)
        change_shipment_status(db, cancelled, ShipmentStatus.Cancelled)
        self.assertEqual(db.query(Notification).filter(Notification.type == "shipment_status").count(), 6)
        db.close()

    def test_driver_assignment_and_explicit_route_recalculation_notify_the_driver(self):
        driver = self.make_driver()
        vehicle = self.make_vehicle()
        response = self.client.post(f"/drivers/{driver.driver_id}/assign-vehicle/{vehicle.vehicle_id}")
        self.assertEqual(response.status_code, 200)
        db = self.db()
        self.assertEqual(
            db.query(Notification).filter(
                Notification.user_id == self.driver_user.user_id,
                Notification.type == "driver_assignment",
            ).count(),
            1,
        )
        shipment = Shipment(
            tracking_number="NOTIFY-ROUTE", source="Coimbatore", destination="Chennai",
            customer_name="Customer", shipment_weight=10, driver_id=driver.driver_id,
            vehicle_id=vehicle.vehicle_id, status=ShipmentStatus.Assigned,
        )
        db.add(shipment)
        db.commit()
        trip = Trip(
            shipment_id=shipment.shipment_id, vehicle_id=vehicle.vehicle_id,
            driver_id=driver.driver_id, source="Coimbatore", destination="Chennai",
            status=TripStatus.Scheduled,
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        db.close()

        route_data = {
            "distance_meters": 12000.0,
            "duration_seconds": 1800.0,
            "geometry": [[76.95, 11.01], [80.27, 13.08]],
            "fallback": False,
        }
        from unittest.mock import patch

        with patch("app.routers.trip.build_route", return_value=route_data):
            self.assertEqual(self.client.post(f"/trips/{trip.trip_id}/route").status_code, 200)
            self.assertEqual(self.client.post(f"/trips/{trip.trip_id}/route").status_code, 200)
        db = self.db()
        self.assertEqual(
            db.query(Notification).filter(Notification.alert_type == f"route_change:{trip.trip_id}").count(),
            1,
        )
        db.close()


if __name__ == "__main__":
    unittest.main()
