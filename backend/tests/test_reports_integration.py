"""Read-only reports and export authorization coverage."""
import unittest
from datetime import date
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from app.core.deps import get_current_user
from app.models.driver import Driver
from app.models.attendance import Attendance
from app.models.fuel_record import FuelRecord
from app.models.maintenance import Maintenance
from app.models.notification import Notification
from app.models.shipment import Shipment
from app.models.trip import Trip
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle, VehicleStatus
from app.services.report_date_range import resolve_report_period


class ReportsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine, expire_on_commit=False)
        Base.metadata.create_all(cls.engine)
        def override_db():
            db = cls.Session()
            try: yield db
            finally: db.close()
        def override_user(): return cls.current_user
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear(); cls.client.close(); Base.metadata.drop_all(cls.engine); cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(self.engine); Base.metadata.create_all(self.engine)
        self.admin = self.user("admin", RoleEnum.Admin); self.manager = self.user("manager", RoleEnum.FleetManager); self.dispatcher = self.user("dispatch", RoleEnum.Dispatcher); self.driver = self.user("driver", RoleEnum.Driver)
        type(self).current_user = SimpleNamespace(user_id=self.admin.user_id, role=self.admin.role)

    def user(self, name, role):
        db = self.Session(); item = User(full_name=name, email=f"{name}@report.test", password="hash", phone="9000000000", role=role, email_verified=True); db.add(item); db.commit(); db.refresh(item); db.close(); return item
    def role(self, user): type(self).current_user = SimpleNamespace(user_id=user.user_id, role=user.role)

    def test_calendar_ranges(self):
        self.assertEqual(resolve_report_period("previous_week", today=date(2026, 8, 26)).as_dict(), {"type":"previous_week", "start_date":"2026-08-17", "end_date":"2026-08-23"})
        self.assertEqual(resolve_report_period("current_week", today=date(2026, 8, 26)).as_dict(), {"type":"current_week", "start_date":"2026-08-24", "end_date":"2026-08-26"})
        self.assertEqual(resolve_report_period("monthly", month=2, year=2028).end_date, date(2028, 2, 29))
        self.assertEqual(resolve_report_period("custom", start_date=date(2026, 8, 1), end_date=date(2026, 8, 2)).start_date, date(2026, 8, 1))
        self.assertEqual(self.client.get("/reports/fleet-utilization?period=custom&start_date=2026-08-02&end_date=2026-08-01").status_code, 400)

    def test_reports_exports_and_rbac(self):
        for path in ["fleet-utilization", "fuel-consumption", "driver-performance", "delivery-performance", "maintenance"]:
            self.assertEqual(self.client.get(f"/reports/{path}?period=current_week").status_code, 200)
            pdf = self.client.get(f"/reports/{path}/export/pdf?period=current_week")
            excel = self.client.get(f"/reports/{path}/export/excel?period=current_week")
            self.assertEqual(pdf.status_code, 200); self.assertEqual(pdf.headers["content-type"], "application/pdf")
            self.assertEqual(excel.status_code, 200); self.assertIn("spreadsheetml", excel.headers["content-type"])
        self.role(self.manager)
        self.assertEqual(self.client.get("/reports/fuel-consumption").status_code, 200)
        self.role(self.dispatcher)
        self.assertEqual(self.client.get("/reports/delivery-performance").status_code, 200)
        for path in ["fleet-utilization", "fuel-consumption", "driver-performance", "maintenance"]:
            self.assertEqual(self.client.get(f"/reports/{path}").status_code, 403)
        self.role(self.driver)
        for path in ["fleet-utilization", "fuel-consumption", "driver-performance", "delivery-performance", "maintenance"]:
            self.assertEqual(self.client.get(f"/reports/{path}").status_code, 403)

if __name__ == "__main__": unittest.main()
