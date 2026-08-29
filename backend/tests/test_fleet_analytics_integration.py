"""Isolated integration coverage for read-only Fleet Performance analytics."""
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_current_user
from app.models.attendance import Attendance, AttendanceActivityType
from app.models.driver import Driver, DriverStatus
from app.models.fuel_record import FuelRecord
from app.models.gps_tracking import GPSTracking
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.notification import Notification
from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip, TripStatus
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle, VehicleStatus
from database import Base, get_db
from main import app


class FleetAnalyticsIntegrationTests(unittest.TestCase):
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
        self.driver_user = self.make_user("driver-user", RoleEnum.Driver)
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
            full_name=label.replace("-", " ").title(),
            email=f"{label}@analytics.test",
            password="test-password-hash",
            phone="9000000000",
            role=role,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        return user

    def make_driver(self, user, suffix):
        db = self.db()
        driver = Driver(
            user_id=user.user_id,
            full_name=user.full_name,
            license_number=f"AN-{suffix}",
            status=DriverStatus.Available,
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        db.close()
        return driver

    def make_vehicle(self, suffix, status=VehicleStatus.Available):
        db = self.db()
        vehicle = Vehicle(
            registration_number=f"TN99AN{suffix}",
            vehicle_type="Truck",
            brand="FleetFlow",
            model="Analytics",
            manufacture_year=2024,
            fuel_type="Diesel",
            capacity=1000,
            status=status,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        db.close()
        return vehicle

    def make_completed_delivery(self, driver, vehicle, suffix, *, expected_offset_hours, duration_hours=1):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        db = self.db()
        shipment = Shipment(
            tracking_number=f"AN-SHIP-{suffix}",
            source="Coimbatore",
            destination="Chennai",
            customer_name="Analytics Customer",
            shipment_weight=50,
            driver_id=driver.driver_id,
            vehicle_id=vehicle.vehicle_id,
            status=ShipmentStatus.Delivered,
            expected_delivery_at=now + timedelta(hours=expected_offset_hours),
        )
        db.add(shipment)
        db.flush()
        trip = Trip(
            shipment_id=shipment.shipment_id,
            vehicle_id=vehicle.vehicle_id,
            driver_id=driver.driver_id,
            source=shipment.source,
            destination=shipment.destination,
            status=TripStatus.Completed,
            route_type="Fastest",
            started_at=now - timedelta(hours=duration_hours),
            ended_at=now,
            planned_distance=10000,
            actual_distance_meters=9500,
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        db.close()
        return trip

    def make_maintenance(self, vehicle, maintenance_type, cost, service_date, status=MaintenanceStatus.Completed):
        db = self.db()
        record = Maintenance(
            vehicle_id=vehicle.vehicle_id,
            maintenance_type=maintenance_type,
            service_date=service_date,
            cost=Decimal(str(cost)),
            status=status,
        )
        db.add(record)
        db.commit()
        db.close()

    def test_fleet_utilization_counts_percentages_and_empty_fleet(self):
        empty = self.client.get("/analytics/fleet-utilization")
        self.assertEqual(empty.status_code, 200, empty.text)
        self.assertEqual(empty.json()["total_fleet"], 0)
        self.assertTrue(all(item["percentage"] == 0 for item in empty.json()["statuses"].values()))

        self.make_vehicle("001", VehicleStatus.Available)
        self.make_vehicle("002", VehicleStatus.Assigned)
        self.make_vehicle("003", VehicleStatus.InTransit)
        self.make_vehicle("004", VehicleStatus.Maintenance)
        response = self.client.get("/analytics/fleet-utilization")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["total_fleet"], 4)
        self.assertEqual(body["statuses"]["Available"], {"count": 1, "percentage": 25.0})
        self.assertEqual(body["statuses"]["In Transit"], {"count": 1, "percentage": 25.0})

    def test_driver_performance_completed_trips_filter_and_attendance_formula(self):
        primary = self.make_driver(self.driver_user, "001")
        other_user = self.make_user("other-driver", RoleEnum.Driver)
        secondary = self.make_driver(other_user, "002")
        vehicle_one = self.make_vehicle("011")
        vehicle_two = self.make_vehicle("012")
        self.make_completed_delivery(primary, vehicle_one, "001", expected_offset_hours=1)
        self.make_completed_delivery(secondary, vehicle_two, "002", expected_offset_hours=-1)

        db = self.db()
        db.add(Attendance(driver_id=primary.driver_id, activity_type=AttendanceActivityType.CheckIn))
        db.commit()
        db.close()

        response = self.client.get("/analytics/driver-performance")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["summary"]["completed_trips"], 2)
        self.assertEqual(body["summary"]["on_time_delivery_rate"], 50.0)
        self.assertEqual(body["summary"]["attendance_rate"], 50.0)

        filtered = self.client.get(f"/analytics/driver-performance?driver_id={primary.driver_id}")
        self.assertEqual(filtered.status_code, 200, filtered.text)
        self.assertEqual(filtered.json()["drivers"][0]["trips_completed"], 1)
        self.assertEqual(filtered.json()["drivers"][0]["attendance_rate"], 100.0)

    def test_driver_performance_rbac(self):
        self.set_role(self.fleet_manager)
        self.assertEqual(self.client.get("/analytics/driver-performance").status_code, 200)
        self.set_role(self.dispatcher)
        self.assertEqual(self.client.get("/analytics/driver-performance").status_code, 403)
        self.assertEqual(self.client.get("/analytics/delivery-performance").status_code, 200)
        self.set_role(self.driver_user)
        self.assertEqual(self.client.get("/analytics/driver-performance").status_code, 403)

    def test_delivery_performance_and_empty_dataset(self):
        empty = self.client.get("/analytics/delivery-performance")
        self.assertEqual(empty.status_code, 200, empty.text)
        self.assertEqual(empty.json()["completed_deliveries"], 0)
        self.assertIsNone(empty.json()["average_delivery_time_seconds"])

        driver = self.make_driver(self.driver_user, "003")
        vehicle = self.make_vehicle("021")
        self.make_completed_delivery(driver, vehicle, "003", expected_offset_hours=2, duration_hours=1)
        self.make_completed_delivery(driver, vehicle, "004", expected_offset_hours=-2, duration_hours=2)
        response = self.client.get("/analytics/delivery-performance")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["completed_deliveries"], 2)
        self.assertEqual(body["on_time_deliveries"], 1)
        self.assertEqual(body["delayed_deliveries"], 1)
        self.assertEqual(body["on_time_rate"], 50.0)
        self.assertEqual(body["average_delivery_time_seconds"], 5400.0)

    def test_maintenance_cost_frequency_and_date_filter(self):
        vehicle = self.make_vehicle("031")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        self.make_maintenance(vehicle, "Oil Change", 120.50, now - timedelta(days=2))
        self.make_maintenance(vehicle, "Brake Service", 75, now)
        self.make_maintenance(vehicle, "Oil Change", 25, now, status=MaintenanceStatus.Scheduled)

        response = self.client.get("/analytics/maintenance")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["completed_maintenance_count"], 2)
        self.assertEqual(body["total_maintenance_cost"], 195.5)
        self.assertEqual(body["cost_by_vehicle"][0]["registration_number"], vehicle.registration_number)
        self.assertEqual(
            {item["maintenance_type"]: item["maintenance_count"] for item in body["frequency_by_type"]},
            {"Oil Change": 1, "Brake Service": 1},
        )

        filtered = self.client.get("/analytics/maintenance", params={"start_date": now.isoformat()})
        self.assertEqual(filtered.status_code, 200, filtered.text)
        self.assertEqual(filtered.json()["total_maintenance_cost"], 75.0)

    def test_operational_summary_and_invalid_date_range(self):
        self.make_vehicle("041", VehicleStatus.Available)
        response = self.client.get("/analytics/operational-summary")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertIn("fleet_utilization", body)
        self.assertIn("driver_performance", body)
        self.assertIn("delivery_performance", body)
        self.assertIn("maintenance_summary", body)

        invalid = self.client.get(
            "/analytics/operational-summary",
            params={"start_date": "2026-12-02T00:00:00Z", "end_date": "2026-12-01T00:00:00Z"},
        )
        self.assertEqual(invalid.status_code, 400)


if __name__ == "__main__":
    unittest.main()
