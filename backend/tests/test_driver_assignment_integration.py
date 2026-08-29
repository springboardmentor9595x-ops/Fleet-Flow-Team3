"""Isolated integration coverage for Driver Assignment backend behavior."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.models.attendance import Attendance, AttendanceActivityType
from app.models.driver import Driver, DriverStatus
from app.models.gps_tracking import GPSTracking
from app.models.maintenance import Maintenance
from app.models.notification import Notification
from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip, TripStatus
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle, VehicleStatus


class DriverAssignmentIntegrationTests(unittest.TestCase):
    """Route-level tests backed by an isolated, in-memory SQLAlchemy database."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False, expire_on_commit=False)

        # Import references above ensure every existing model is represented in
        # Base.metadata before test tables are created.
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
        self.driver_user = self.make_user("driver-one", RoleEnum.Driver)
        self.other_driver_user = self.make_user("driver-two", RoleEnum.Driver)
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
            email=f"{label}@test.local",
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

    def make_driver(self, user, *, license_number="DL-100", status=DriverStatus.Available):
        db = self.db()
        driver = Driver(
            user_id=user.user_id,
            full_name=user.full_name,
            license_number=license_number,
            experience_years=4,
            address="Coimbatore",
            status=status,
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
        db.close()
        return driver

    def make_vehicle(self, suffix="001", *, status=VehicleStatus.Available, assigned_driver=None):
        db = self.db()
        vehicle = Vehicle(
            registration_number=f"TN99TEST{suffix}",
            vehicle_type="Truck",
            brand="FleetFlow",
            model="Test",
            manufacture_year=2024,
            fuel_type="Diesel",
            capacity=1000,
            status=status,
            assigned_driver=assigned_driver,
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        db.close()
        return vehicle

    def make_shipment(self, suffix="001", *, driver_id=None, vehicle_id=None, status=ShipmentStatus.Assigned):
        db = self.db()
        shipment = Shipment(
            tracking_number=f"TRACK-{suffix}",
            source="Coimbatore",
            destination="Chennai",
            customer_name="Integration Customer",
            shipment_weight=100.0,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            status=status,
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        db.close()
        return shipment

    def make_trip(self, driver, vehicle, shipment, *, status=TripStatus.Scheduled):
        db = self.db()
        trip = Trip(
            driver_id=driver.driver_id,
            vehicle_id=vehicle.vehicle_id,
            shipment_id=shipment.shipment_id,
            source="Coimbatore",
            destination="Chennai",
            status=status,
            route_type="Fastest",
            planned_distance=10000.0,
            estimated_duration=1200.0,
            route_geometry=[[76.9, 11.0], [77.1, 13.0]],
        )
        db.add(trip)
        db.commit()
        db.refresh(trip)
        db.close()
        return trip

    def driver_payload(self, user, *, license_number="DL-NEW"):
        return {
            "full_name": user.full_name,
            "user_id": str(user.user_id),
            "license_number": license_number,
            "experience_years": 3,
            "address": "Chennai",
            "status": "Available",
        }

    def test_driver_registration_validation_and_duplicate_license(self):
        response = self.client.post("/drivers/", json=self.driver_payload(self.driver_user, license_number="DL-1"))
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["status"], "Available")

        duplicate = self.client.post("/drivers/", json=self.driver_payload(self.driver_user, license_number="DL-2"))
        self.assertEqual(duplicate.status_code, 400)

        duplicate_license = self.client.post("/drivers/", json=self.driver_payload(self.other_driver_user, license_number="DL-1"))
        self.assertEqual(duplicate_license.status_code, 400)

        missing_user = self.client.post("/drivers/", json={**self.driver_payload(self.other_driver_user), "user_id": "00000000-0000-0000-0000-000000000001"})
        self.assertEqual(missing_user.status_code, 404)

        non_driver = self.client.post("/drivers/", json=self.driver_payload(self.dispatcher, license_number="DL-3"))
        self.assertEqual(non_driver.status_code, 400)

    def test_admin_and_fleet_manager_can_manage_and_dispatcher_driver_cannot(self):
        created = self.client.post("/drivers/", json=self.driver_payload(self.driver_user, license_number="DL-4"))
        self.assertEqual(created.status_code, 201, created.text)
        driver_id = created.json()["driver_id"]

        admin_updated = self.client.put(f"/drivers/{driver_id}", json={"address": "Admin updated"})
        self.assertEqual(admin_updated.status_code, 200, admin_updated.text)

        self.set_role(self.fleet_manager)
        updated = self.client.put(f"/drivers/{driver_id}", json={"experience_years": 7})
        self.assertEqual(updated.status_code, 200, updated.text)
        self.assertEqual(updated.json()["experience_years"], 7)
        fleet_driver_user = self.make_user("driver-four", RoleEnum.Driver)
        fleet_created = self.client.post("/drivers/", json=self.driver_payload(fleet_driver_user, license_number="DL-4-FM"))
        self.assertEqual(fleet_created.status_code, 201, fleet_created.text)
        self.assertEqual(self.client.delete(f"/drivers/{fleet_created.json()['driver_id']}").status_code, 204)

        self.set_role(self.dispatcher)
        self.assertEqual(self.client.post("/drivers/", json=self.driver_payload(self.other_driver_user, license_number="DL-5")).status_code, 403)
        self.assertEqual(self.client.put(f"/drivers/{driver_id}", json={"address": "Blocked"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/drivers/{driver_id}").status_code, 403)

        self.set_role(self.driver_user)
        self.assertEqual(self.client.put(f"/drivers/{driver_id}", json={"address": "Blocked"}).status_code, 403)

        self.set_role(self.admin)
        self.assertEqual(self.client.delete(f"/drivers/{driver_id}").status_code, 204)

    def test_driver_can_only_read_own_profile(self):
        own = self.make_driver(self.driver_user, license_number="DL-6")
        other = self.make_driver(self.other_driver_user, license_number="DL-7")
        self.set_role(self.driver_user)

        listing = self.client.get("/drivers/")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item["driver_id"] for item in listing.json()], [str(own.driver_id)])
        self.assertEqual(self.client.get(f"/drivers/{own.driver_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/drivers/{other.driver_id}").status_code, 403)

    def test_assign_reassign_and_unassign_vehicle(self):
        driver = self.make_driver(self.driver_user, license_number="DL-8")
        first_vehicle = self.make_vehicle("008")
        second_vehicle = self.make_vehicle("009")

        assigned = self.client.post(f"/drivers/{driver.driver_id}/assign-vehicle/{first_vehicle.vehicle_id}")
        self.assertEqual(assigned.status_code, 200, assigned.text)
        self.assertEqual(assigned.json()["assigned_vehicle_id"], str(first_vehicle.vehicle_id))

        reassigned = self.client.post(f"/drivers/{driver.driver_id}/reassign-vehicle/{second_vehicle.vehicle_id}")
        self.assertEqual(reassigned.status_code, 200, reassigned.text)
        self.assertEqual(reassigned.json()["assigned_vehicle_id"], str(second_vehicle.vehicle_id))

        unassigned = self.client.delete(f"/drivers/{driver.driver_id}/unassign-vehicle")
        self.assertEqual(unassigned.status_code, 200, unassigned.text)
        self.assertIsNone(unassigned.json()["assigned_vehicle_id"])

    def test_assignment_rejects_inactive_maintenance_unavailable_and_reserved_resources(self):
        inactive = self.make_driver(self.driver_user, license_number="DL-9", status=DriverStatus.Inactive)
        available_vehicle = self.make_vehicle("010")
        self.assertEqual(self.client.post(f"/drivers/{inactive.driver_id}/assign-vehicle/{available_vehicle.vehicle_id}").status_code, 400)

        active_driver = self.make_driver(self.other_driver_user, license_number="DL-10")
        maintenance_vehicle = self.make_vehicle("011", status=VehicleStatus.Maintenance)
        self.assertEqual(self.client.post(f"/drivers/{active_driver.driver_id}/assign-vehicle/{maintenance_vehicle.vehicle_id}").status_code, 400)

        unavailable_vehicle = self.make_vehicle("012", status=VehicleStatus.InTransit)
        self.assertEqual(self.client.post(f"/drivers/{active_driver.driver_id}/assign-vehicle/{unavailable_vehicle.vehicle_id}").status_code, 400)

        reserved_vehicle = self.make_vehicle("013")
        reserved_shipment = self.make_shipment("013", driver_id=active_driver.driver_id, vehicle_id=reserved_vehicle.vehicle_id)
        self.make_trip(active_driver, reserved_vehicle, reserved_shipment, status=TripStatus.Scheduled)
        target_vehicle = self.make_vehicle("014")
        self.assertEqual(self.client.post(f"/drivers/{active_driver.driver_id}/assign-vehicle/{target_vehicle.vehicle_id}").status_code, 400)
        fresh_driver = self.make_driver(self.make_user("driver-three", RoleEnum.Driver), license_number="DL-11")
        self.assertEqual(self.client.post(f"/drivers/{fresh_driver.driver_id}/assign-vehicle/{reserved_vehicle.vehicle_id}").status_code, 400)

    def test_reassign_and_unassign_cannot_break_reserved_trip(self):
        driver = self.make_driver(self.driver_user, license_number="DL-11-R")
        assigned_vehicle = self.make_vehicle("018", assigned_driver=driver.driver_id)
        replacement_vehicle = self.make_vehicle("019")
        shipment = self.make_shipment("018", driver_id=driver.driver_id, vehicle_id=assigned_vehicle.vehicle_id)
        self.make_trip(driver, assigned_vehicle, shipment, status=TripStatus.Scheduled)

        self.assertEqual(self.client.post(f"/drivers/{driver.driver_id}/reassign-vehicle/{replacement_vehicle.vehicle_id}").status_code, 400)
        self.assertEqual(self.client.delete(f"/drivers/{driver.driver_id}/unassign-vehicle").status_code, 400)

    def test_attendance_check_in_and_check_out_rules(self):
        driver = self.make_driver(self.driver_user, license_number="DL-12")
        self.set_role(self.driver_user)

        self.assertEqual(self.client.post("/attendance/check-in", json={"notes": "Morning shift"}).status_code, 201)
        self.assertEqual(self.client.post("/attendance/check-in", json={}).status_code, 400)
        self.assertEqual(self.client.post("/attendance/check-out", json={"notes": "Shift closed"}).status_code, 201)
        self.assertEqual(self.client.post("/attendance/check-out", json={}).status_code, 400)

        mine = self.client.get("/attendance/me")
        self.assertEqual(mine.status_code, 200)
        self.assertEqual({entry["activity_type"] for entry in mine.json()}, {"Attendance / Check-in", "Attendance / Check-out"})

        other = self.make_driver(self.other_driver_user, license_number="DL-13")
        self.assertEqual(self.client.get(f"/attendance/driver/{other.driver_id}").status_code, 403)
        self.assertEqual(self.client.get(f"/attendance/driver/{driver.driver_id}").status_code, 200)

    def test_start_and_end_trip_create_activity_and_update_status(self):
        driver = self.make_driver(self.driver_user, license_number="DL-14", status=DriverStatus.Offline)
        vehicle = self.make_vehicle("015", status=VehicleStatus.Assigned, assigned_driver=driver.driver_id)
        shipment = self.make_shipment("015", driver_id=driver.driver_id, vehicle_id=vehicle.vehicle_id)
        trip = self.make_trip(driver, vehicle, shipment)

        with patch("app.routers.trip.gps_simulator.start", new=AsyncMock()), patch("app.routers.trip.gps_simulator.stop", new=AsyncMock()):
            started = self.client.patch(f"/trips/{trip.trip_id}/start")
            self.assertEqual(started.status_code, 200, started.text)

            db = self.db()
            refreshed_driver = db.get(Driver, driver.driver_id)
            self.assertEqual(refreshed_driver.status, DriverStatus.OnTrip)
            self.assertEqual(db.query(Attendance).filter(Attendance.trip_id == trip.trip_id, Attendance.activity_type == AttendanceActivityType.TripStarted).count(), 1)
            db.close()

            ended = self.client.patch(f"/trips/{trip.trip_id}/end", json={"actual_distance_meters": 9500})
            self.assertEqual(ended.status_code, 200, ended.text)

        db = self.db()
        refreshed_driver = db.get(Driver, driver.driver_id)
        self.assertEqual(refreshed_driver.status, DriverStatus.Available)
        self.assertEqual(db.query(Attendance).filter(Attendance.trip_id == trip.trip_id, Attendance.activity_type == AttendanceActivityType.TripCompleted).count(), 1)
        db.close()

    def test_ending_trip_preserves_manually_inactive_status(self):
        driver = self.make_driver(self.driver_user, license_number="DL-15", status=DriverStatus.Inactive)
        vehicle = self.make_vehicle("016", status=VehicleStatus.InTransit, assigned_driver=driver.driver_id)
        shipment = self.make_shipment("016", driver_id=driver.driver_id, vehicle_id=vehicle.vehicle_id, status=ShipmentStatus.InTransit)
        trip = self.make_trip(driver, vehicle, shipment, status=TripStatus.Active)

        with patch("app.routers.trip.gps_simulator.stop", new=AsyncMock()):
            ended = self.client.patch(f"/trips/{trip.trip_id}/end", json={})
        self.assertEqual(ended.status_code, 200, ended.text)

        db = self.db()
        self.assertEqual(db.get(Driver, driver.driver_id).status, DriverStatus.Inactive)
        self.assertEqual(db.query(Attendance).filter(Attendance.trip_id == trip.trip_id, Attendance.activity_type == AttendanceActivityType.TripCompleted).count(), 1)
        db.close()

    def test_scheduled_trip_deletion_releases_driver_and_vehicle(self):
        driver = self.make_driver(self.driver_user, license_number="DL-16", status=DriverStatus.Offline)
        vehicle = self.make_vehicle("017", status=VehicleStatus.Assigned, assigned_driver=driver.driver_id)
        shipment = self.make_shipment("017", driver_id=driver.driver_id, vehicle_id=vehicle.vehicle_id)
        trip = self.make_trip(driver, vehicle, shipment)

        deleted = self.client.delete(f"/trips/{trip.trip_id}")
        self.assertEqual(deleted.status_code, 204, deleted.text)

        db = self.db()
        self.assertEqual(db.get(Driver, driver.driver_id).status, DriverStatus.Available)
        refreshed_vehicle = db.get(Vehicle, vehicle.vehicle_id)
        self.assertEqual(refreshed_vehicle.status, VehicleStatus.Available)
        self.assertIsNone(refreshed_vehicle.assigned_driver)
        db.close()

    def test_rbac_matrix_protects_vehicle_dashboard_shipment_and_gps_resources(self):
        own_driver = self.make_driver(self.driver_user, license_number="RBAC-OWN")
        other_driver = self.make_driver(self.other_driver_user, license_number="RBAC-OTHER")
        own_vehicle = self.make_vehicle("RBAC1", assigned_driver=own_driver.driver_id)
        other_vehicle = self.make_vehicle("RBAC2", assigned_driver=other_driver.driver_id)

        self.set_role(self.dispatcher)
        self.assertEqual(self.client.post("/vehicles/", json={}).status_code, 403)
        self.assertEqual(self.client.put(f"/vehicles/{own_vehicle.vehicle_id}", json={}).status_code, 403)
        self.assertEqual(self.client.delete(f"/vehicles/{own_vehicle.vehicle_id}").status_code, 403)
        self.assertEqual(self.client.get("/dashboard/fleet").status_code, 403)
        self.assertEqual(self.client.post("/gps/location", json={
            "vehicle_id": str(own_vehicle.vehicle_id), "latitude": 11.0, "longitude": 76.0, "speed": 20,
        }).status_code, 403)

        self.set_role(self.driver_user)
        self.assertEqual(self.client.get(f"/vehicles/{own_vehicle.vehicle_id}").status_code, 200)
        self.assertEqual(self.client.get(f"/vehicles/{other_vehicle.vehicle_id}").status_code, 403)
        self.assertEqual(self.client.get("/dashboard/fleet").status_code, 403)
        self.assertEqual(self.client.post("/gps/location", json={
            "vehicle_id": str(own_vehicle.vehicle_id), "latitude": 11.0, "longitude": 76.0, "speed": 20,
        }).status_code, 200)
        self.assertEqual(self.client.post("/gps/location", json={
            "vehicle_id": str(other_vehicle.vehicle_id), "latitude": 11.0, "longitude": 76.0, "speed": 20,
        }).status_code, 403)
        self.assertEqual(self.client.get(f"/gps/latest/{other_vehicle.vehicle_id}").status_code, 403)

        self.set_role(self.fleet_manager)
        self.assertEqual(self.client.get("/dashboard/fleet").status_code, 200)
        self.assertEqual(self.client.get("/analytics/operational-summary").status_code, 403)
        self.assertEqual(self.client.get("/analytics/delivery-performance").status_code, 200)

    def test_public_signup_cannot_create_a_privileged_role(self):
        response = self.client.post("/auth/signup", json={
            "email": "attempted-admin@example.com",
            "password": "safe-password",
            "full_name": "Attempted Admin",
            "phone": "9000000000",
            "role": "Admin",
        })
        self.assertEqual(response.status_code, 403, response.text)

    def test_dispatcher_can_manage_shipments_but_driver_cannot(self):
        self.set_role(self.dispatcher)
        payload = {
            "tracking_number": "RBAC-SHIP-1",
            "source": "Coimbatore",
            "destination": "Chennai",
            "customer_name": "RBAC Customer",
            "shipment_weight": 100,
        }
        created = self.client.post("/shipments/", json=payload)
        self.assertEqual(created.status_code, 201, created.text)
        shipment_id = created.json()["shipment_id"]
        self.assertEqual(self.client.put(f"/shipments/{shipment_id}", json={"customer_name": "Updated Customer"}).status_code, 200)

        self.set_role(self.driver_user)
        self.assertEqual(self.client.put(f"/shipments/{shipment_id}", json={"customer_name": "Blocked"}).status_code, 403)

    def test_websocket_denies_driver_subscription_to_another_vehicle(self):
        own_driver = self.make_driver(self.driver_user, license_number="WS-OWN")
        other_driver = self.make_driver(self.other_driver_user, license_number="WS-OTHER")
        own_vehicle = self.make_vehicle("WS1", assigned_driver=own_driver.driver_id)
        other_vehicle = self.make_vehicle("WS2", assigned_driver=other_driver.driver_id)
        token = create_access_token({"sub": self.driver_user.email})

        with patch("app.routers.gps_tracking.SessionLocal", self.Session):
            with self.client.websocket_connect(f"/gps/ws/{own_vehicle.vehicle_id}?token={token}") as socket:
                socket.send_json({"type": "heartbeat"})
                self.assertEqual(socket.receive_json()["type"], "heartbeat_ack")
            with self.assertRaises(Exception):
                with self.client.websocket_connect(f"/gps/ws/{other_vehicle.vehicle_id}?token={token}"):
                    pass


if __name__ == "__main__":
    unittest.main()
