"""Isolated integration coverage for Fuel Monitoring Analytics."""
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_current_user
from app.models.attendance import Attendance
from app.models.driver import Driver
from app.models.fuel_record import FuelRecord
from app.models.gps_tracking import GPSTracking
from app.models.maintenance import Maintenance
from app.models.notification import Notification
from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip, TripStatus
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle, VehicleStatus
from database import Base, get_db
from main import app


class FuelMonitoringIntegrationTests(unittest.TestCase):
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
        self.driver = self.make_driver(self.driver_user)
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
            full_name=label.title(),
            email=f"{label}@fuel.test",
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

    def make_driver(self, user):
        db = self.db()
        driver = Driver(user_id=user.user_id, full_name=user.full_name, license_number="FUEL-001")
        db.add(driver)
        db.commit()
        db.refresh(driver)
        db.close()
        return driver

    def make_vehicle(self, suffix, *, assigned_driver=None):
        db = self.db()
        vehicle = Vehicle(
            registration_number=f"TN99FUEL{suffix}",
            vehicle_type="Truck",
            brand="FleetFlow",
            model="Fuel Test",
            manufacture_year=2024,
            fuel_type="Diesel",
            capacity=1000,
            status=VehicleStatus.Available,
            assigned_driver=assigned_driver,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        db.close()
        return vehicle

    def fuel_payload(self, vehicle, *, amount=20, cost=2000, mileage=10000, refill_date=None):
        return {
            "vehicle_id": str(vehicle.vehicle_id),
            "fuel_amount": amount,
            "fuel_cost": cost,
            "mileage": mileage,
            "refill_date": (refill_date or datetime.now(timezone.utc)).isoformat(),
        }

    def make_completed_trip(self, vehicle, suffix, *, actual_distance=None, planned_distance=None, ended_at=None):
        ended_at = ended_at or datetime.now(timezone.utc)
        db = self.db()
        shipment = Shipment(
            tracking_number=f"FUEL-SHIP-{suffix}",
            source="Coimbatore",
            destination="Chennai",
            customer_name="Fuel Customer",
            shipment_weight=100,
            vehicle_id=vehicle.vehicle_id,
            driver_id=self.driver.driver_id,
            status=ShipmentStatus.Delivered,
        )
        db.add(shipment)
        db.flush()
        trip = Trip(
            shipment_id=shipment.shipment_id,
            vehicle_id=vehicle.vehicle_id,
            driver_id=self.driver.driver_id,
            source="Coimbatore",
            destination="Chennai",
            route_type="Fastest",
            status=TripStatus.Completed,
            started_at=ended_at - timedelta(hours=2),
            ended_at=ended_at,
            actual_distance_meters=actual_distance,
            planned_distance=planned_distance,
        )
        db.add(trip)
        db.commit()
        db.close()

    def test_fuel_record_create_validation_and_vehicle_reference(self):
        vehicle = self.make_vehicle("001")
        created = self.client.post("/fuel-records/", json=self.fuel_payload(vehicle))
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["fuel_amount"], "20.000")
        self.assertRegex(created.json()["fuel_reference"], r"^FUEL-\d{4,}$")

        invalid_amount = self.client.post("/fuel-records/", json=self.fuel_payload(vehicle, amount=0))
        self.assertEqual(invalid_amount.status_code, 422)
        invalid_date = self.client.post("/fuel-records/", json={**self.fuel_payload(vehicle), "refill_date": "not-a-date"})
        self.assertEqual(invalid_date.status_code, 422)
        missing_vehicle = self.client.post(
            "/fuel-records/",
            json={**self.fuel_payload(vehicle), "vehicle_id": "00000000-0000-0000-0000-000000000001"},
        )
        self.assertEqual(missing_vehicle.status_code, 404)

    def test_fuel_record_retrieval_update_and_delete(self):
        vehicle = self.make_vehicle("002")
        created = self.client.post("/fuel-records/", json=self.fuel_payload(vehicle)).json()
        fuel_id = created["fuel_id"]
        self.assertEqual(self.client.get("/fuel-records/").status_code, 200)
        self.assertEqual(self.client.get(f"/fuel-records/{fuel_id}").status_code, 200)

        updated = self.client.put(f"/fuel-records/{fuel_id}", json={"fuel_cost": 2250, "mileage": 10250})
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["fuel_cost"], "2250.00")
        self.assertEqual(self.client.delete(f"/fuel-records/{fuel_id}").status_code, 204)
        self.assertEqual(self.client.get(f"/fuel-records/{fuel_id}").status_code, 404)

    def test_fuel_record_rbac(self):
        vehicle = self.make_vehicle("003")
        created = self.client.post("/fuel-records/", json=self.fuel_payload(vehicle)).json()
        fuel_id = created["fuel_id"]

        self.set_role(self.fleet_manager)
        self.assertEqual(self.client.post("/fuel-records/", json=self.fuel_payload(vehicle)).status_code, 201)
        self.assertEqual(self.client.get("/fuel-records/").status_code, 200)
        self.assertEqual(self.client.put(f"/fuel-records/{fuel_id}", json={"fuel_cost": 2200}).status_code, 200)
        self.assertEqual(self.client.delete(f"/fuel-records/{fuel_id}").status_code, 204)

        created = self.client.post("/fuel-records/", json=self.fuel_payload(vehicle)).json()
        fuel_id = created["fuel_id"]
        self.set_role(self.dispatcher)
        self.assertEqual(self.client.get("/fuel-records/").status_code, 200)
        self.assertEqual(self.client.get(f"/fuel-records/{fuel_id}").status_code, 200)
        self.assertEqual(self.client.post("/fuel-records/", json=self.fuel_payload(vehicle)).status_code, 403)
        self.assertEqual(self.client.put(f"/fuel-records/{fuel_id}", json={"fuel_cost": 2200}).status_code, 403)
        self.assertEqual(self.client.delete(f"/fuel-records/{fuel_id}").status_code, 403)
        self.assertEqual(self.client.get("/analytics/fuel-cost-trends").status_code, 403)

        self.set_role(self.driver_user)
        self.assertEqual(self.client.get("/fuel-records/").status_code, 200)
        self.assertEqual(self.client.get("/fuel-records/").json(), [])
        self.assertEqual(self.client.get("/analytics/fuel-efficiency").status_code, 403)

    def test_driver_can_only_read_fuel_records_for_assigned_vehicle(self):
        own_vehicle = self.make_vehicle("DRIVER1", assigned_driver=self.driver.driver_id)
        other_vehicle = self.make_vehicle("DRIVER2")
        own_record = self.client.post("/fuel-records/", json=self.fuel_payload(own_vehicle)).json()
        other_record = self.client.post("/fuel-records/", json=self.fuel_payload(other_vehicle)).json()

        self.set_role(self.driver_user)
        listed = self.client.get("/fuel-records/", params={"vehicle_id": str(other_vehicle.vehicle_id)})
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual([item["fuel_id"] for item in listed.json()], [own_record["fuel_id"]])
        self.assertEqual(self.client.get(f"/fuel-records/{own_record['fuel_id']}").status_code, 200)
        self.assertEqual(self.client.get(f"/fuel-records/{other_record['fuel_id']}").status_code, 403)
        self.assertEqual(self.client.post("/fuel-records/", json=self.fuel_payload(own_vehicle)).status_code, 403)
        self.assertEqual(self.client.put(f"/fuel-records/{own_record['fuel_id']}", json={"fuel_cost": 2250}).status_code, 403)
        self.assertEqual(self.client.delete(f"/fuel-records/{own_record['fuel_id']}").status_code, 403)

    def test_fuel_efficiency_distinguishes_actual_estimated_and_missing_distance(self):
        vehicle = self.make_vehicle("004")
        self.client.post("/fuel-records/", json=self.fuel_payload(vehicle, amount=10, cost=1000))
        self.make_completed_trip(vehicle, "004A", actual_distance=8000, planned_distance=10000)
        self.make_completed_trip(vehicle, "004B", actual_distance=None, planned_distance=5000)
        self.make_completed_trip(vehicle, "004C", actual_distance=None, planned_distance=None)

        response = self.client.get("/analytics/fuel-efficiency")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["actual_distance_meters"], 8000.0)
        self.assertEqual(body["estimated_distance_meters"], 5000.0)
        self.assertEqual(body["distance_used_meters"], 13000.0)
        self.assertEqual(body["fuel_efficiency_km_per_fuel_unit"], 1.3)
        self.assertEqual(body["vehicles"][0]["completed_trips"], 2)

    def test_fuel_cost_trends_multiple_vehicles_date_filter_and_empty_dataset(self):
        empty = self.client.get("/analytics/fuel-cost-trends")
        self.assertEqual(empty.status_code, 200, empty.text)
        self.assertEqual(empty.json()["total_refills"], 0)

        first = self.make_vehicle("005")
        second = self.make_vehicle("006")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        self.client.post("/fuel-records/", json=self.fuel_payload(first, amount=20, cost=2000, refill_date=now - timedelta(days=2)))
        self.client.post("/fuel-records/", json=self.fuel_payload(first, amount=10, cost=1100, refill_date=now))
        self.client.post("/fuel-records/", json=self.fuel_payload(second, amount=15, cost=1500, refill_date=now))

        response = self.client.get("/analytics/fuel-cost-trends")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["total_refills"], 3)
        self.assertEqual(body["total_fuel_consumed"], 45.0)
        self.assertEqual(body["total_fuel_cost"], 4600.0)
        self.assertEqual(len(body["cost_by_vehicle"]), 2)
        self.assertEqual(len(body["cost_over_time"]), 2)

        filtered = self.client.get("/analytics/fuel-cost-trends", params={"start_date": now.isoformat()})
        self.assertEqual(filtered.status_code, 200, filtered.text)
        self.assertEqual(filtered.json()["total_fuel_cost"], 2600.0)


if __name__ == "__main__":
    unittest.main()
