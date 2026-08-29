"""Isolated integration coverage for maintenance reminder scheduling rules."""
import unittest
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.driver import Driver
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.notification import Notification
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.tasks.maintenance import process_maintenance_alerts
from database import Base


class MaintenanceNotificationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.now = datetime(2026, 8, 25, 9, tzinfo=timezone.utc)
        db = self.Session()
        self.vehicle = Vehicle(
            registration_number="TN99MN001",
            vehicle_type="Truck",
            brand="FleetFlow",
            model="Maintenance Test",
            manufacture_year=2024,
            fuel_type="Diesel",
            capacity=1000,
            status=VehicleStatus.Available,
        )
        db.add(self.vehicle)
        db.commit()
        db.refresh(self.vehicle)
        db.close()

    def make_maintenance(self, days_from_now, status=MaintenanceStatus.Scheduled):
        db = self.Session()
        maintenance = Maintenance(
            vehicle_id=self.vehicle.vehicle_id,
            maintenance_type="Oil Change",
            service_date=self.now + timedelta(days=days_from_now),
            status=status,
        )
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
        db.close()
        return maintenance

    def notification_types(self):
        db = self.Session()
        values = [item.alert_type for item in db.query(Notification).order_by(Notification.sent_at).all()]
        db.close()
        return values

    def test_five_day_reminder_is_created_once(self):
        self.make_maintenance(5)
        db = self.Session()
        self.assertEqual(process_maintenance_alerts(db, self.now)["five_day"], 1)
        repeat = process_maintenance_alerts(db, self.now)
        self.assertEqual(repeat["five_day"], 1)
        self.assertEqual(repeat["five_day_created"], 0)
        db.close()
        self.assertEqual(self.notification_types(), ["due_in_5_days"])

    def test_one_day_reminder_is_created_once(self):
        self.make_maintenance(1)
        db = self.Session()
        self.assertEqual(process_maintenance_alerts(db, self.now)["one_day"], 1)
        repeat = process_maintenance_alerts(db, self.now)
        self.assertEqual(repeat["one_day"], 1)
        self.assertEqual(repeat["one_day_created"], 0)
        db.close()
        self.assertEqual(self.notification_types(), ["due_tomorrow"])

    def test_due_today_and_overdue_repeat_daily_while_unresolved(self):
        self.make_maintenance(0)
        db = self.Session()
        self.assertEqual(process_maintenance_alerts(db, self.now)["due_today"], 1)
        first_overdue = self.now + timedelta(days=1)
        second_overdue = self.now + timedelta(days=2)
        self.assertEqual(process_maintenance_alerts(db, first_overdue)["overdue"], 1)
        self.assertEqual(process_maintenance_alerts(db, second_overdue)["overdue"], 1)
        db.close()
        self.assertEqual(self.notification_types(), ["due_today", "overdue_2026-08-26", "overdue_2026-08-27"])

    def test_resolved_record_stops_future_notifications(self):
        maintenance = self.make_maintenance(0)
        db = self.Session()
        self.assertEqual(process_maintenance_alerts(db, self.now)["due_today"], 1)
        record = db.query(Maintenance).filter(Maintenance.maintenance_id == maintenance.maintenance_id).first()
        record.status = MaintenanceStatus.Resolved
        db.commit()
        self.assertEqual(process_maintenance_alerts(db, self.now + timedelta(days=1))["overdue"], 0)
        db.close()
        self.assertEqual(self.notification_types(), ["due_today"])

    def test_overdue_scheduled_record_is_detected_when_daily_notification_exists(self):
        self.make_maintenance(-4)
        db = self.Session()
        first = process_maintenance_alerts(db, self.now)
        self.assertEqual(first["overdue"], 1)
        self.assertEqual(first["overdue_created"], 1)
        repeat = process_maintenance_alerts(db, self.now)
        self.assertEqual(repeat["overdue"], 1)
        self.assertEqual(repeat["overdue_created"], 0)
        db.close()
        self.assertEqual(self.notification_types(), ["overdue_2026-08-25"])

    def test_completed_and_cancelled_records_are_compatible_and_silent(self):
        self.make_maintenance(-2, MaintenanceStatus.Completed)
        self.make_maintenance(-2, MaintenanceStatus.Cancelled)
        db = self.Session()
        result = process_maintenance_alerts(db, self.now)
        self.assertEqual(result["overdue"], 0)
        self.assertEqual(result["overdue_created"], 0)
        db.close()
        self.assertEqual(self.notification_types(), [])

    def test_empty_table_is_safe(self):
        db = self.Session()
        result = process_maintenance_alerts(db, self.now)
        self.assertEqual(result["five_day"], 0)
        self.assertEqual(result["overdue"], 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
