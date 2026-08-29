from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_fleet_analytics, require_logistics_analytics
from app.schemas.report import ReportResponse
from app.services.report_date_range import ReportPeriod, resolve_report_period
from app.services.report_exports import report_excel, report_pdf
from app.services.reports import delivery_performance_report, driver_performance_report, fleet_utilization_report, fuel_consumption_report, maintenance_report
from database import get_db

router = APIRouter(prefix="/reports", tags=["Reports & Export"])

def report_period(period: str = Query(default="current_week"), month: int | None = Query(default=None), year: int | None = Query(default=None), start_date: date | None = Query(default=None), end_date: date | None = Query(default=None)) -> ReportPeriod:
    return resolve_report_period(period, month, year, start_date, end_date)

def export_response(report: dict, kind: str):
    filename = f"{report['report_type']}_{report['period']['start_date']}_{report['period']['end_date']}"
    if kind == "pdf":
        return StreamingResponse(report_pdf(report), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})
    return StreamingResponse(report_excel(report), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'})

@router.get("/fleet-utilization", response_model=ReportResponse)
def fleet_utilization(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return fleet_utilization_report(db, period)
@router.get("/fleet-utilization/export/pdf")
def fleet_utilization_pdf(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(fleet_utilization_report(db, period), "pdf")
@router.get("/fleet-utilization/export/excel")
def fleet_utilization_excel(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(fleet_utilization_report(db, period), "excel")

@router.get("/fuel-consumption", response_model=ReportResponse)
def fuel_consumption(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return fuel_consumption_report(db, period)
@router.get("/fuel-consumption/export/pdf")
def fuel_consumption_pdf(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(fuel_consumption_report(db, period), "pdf")
@router.get("/fuel-consumption/export/excel")
def fuel_consumption_excel(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(fuel_consumption_report(db, period), "excel")

@router.get("/driver-performance", response_model=ReportResponse)
def driver_performance(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return driver_performance_report(db, period)
@router.get("/driver-performance/export/pdf")
def driver_performance_pdf(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(driver_performance_report(db, period), "pdf")
@router.get("/driver-performance/export/excel")
def driver_performance_excel(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(driver_performance_report(db, period), "excel")

@router.get("/delivery-performance", response_model=ReportResponse)
def delivery_performance(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_logistics_analytics)): return delivery_performance_report(db, period)
@router.get("/delivery-performance/export/pdf")
def delivery_performance_pdf(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_logistics_analytics)): return export_response(delivery_performance_report(db, period), "pdf")
@router.get("/delivery-performance/export/excel")
def delivery_performance_excel(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_logistics_analytics)): return export_response(delivery_performance_report(db, period), "excel")

@router.get("/maintenance", response_model=ReportResponse)
def maintenance(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return maintenance_report(db, period)
@router.get("/maintenance/export/pdf")
def maintenance_pdf(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(maintenance_report(db, period), "pdf")
@router.get("/maintenance/export/excel")
def maintenance_excel(period: ReportPeriod = Depends(report_period), db: Session = Depends(get_db), current_user=Depends(require_fleet_analytics)): return export_response(maintenance_report(db, period), "excel")
