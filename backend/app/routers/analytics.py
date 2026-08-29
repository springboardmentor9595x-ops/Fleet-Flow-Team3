from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import (
    require_admin,
    require_fleet_analytics,
    require_logistics_analytics,
)
from app.schemas.analytics import (
    DeliveryPerformanceResponse,
    DriverPerformanceResponse,
    FleetUtilizationResponse,
    FuelCostTrendsResponse,
    FuelEfficiencyResponse,
    MaintenanceAnalyticsResponse,
    OperationalSummaryResponse,
)
from app.services.analytics import (
    delivery_performance,
    driver_performance,
    fleet_utilization,
    fuel_cost_trends,
    fuel_efficiency,
    maintenance_analytics,
    operational_summary,
)
from database import get_db


router = APIRouter(prefix="/analytics", tags=["Fleet Performance & Operational Analytics"])


def validate_date_range(start_date: datetime | None, end_date: datetime | None) -> None:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be earlier than or equal to end_date.",
        )


@router.get("/fleet-utilization", response_model=FleetUtilizationResponse)
def get_fleet_utilization(
    db: Session = Depends(get_db),
    current_user=Depends(require_fleet_analytics),
):
    return fleet_utilization(db)


@router.get("/driver-performance", response_model=DriverPerformanceResponse)
def get_driver_performance(
    driver_id: UUID | None = None,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_fleet_analytics),
):
    validate_date_range(start_date, end_date)
    return driver_performance(db, driver_id=driver_id, start_date=start_date, end_date=end_date)


@router.get("/delivery-performance", response_model=DeliveryPerformanceResponse)
def get_delivery_performance(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_logistics_analytics),
):
    validate_date_range(start_date, end_date)
    return delivery_performance(db, start_date=start_date, end_date=end_date)


@router.get("/maintenance", response_model=MaintenanceAnalyticsResponse)
def get_maintenance_analytics(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_fleet_analytics),
):
    validate_date_range(start_date, end_date)
    return maintenance_analytics(db, start_date=start_date, end_date=end_date)


@router.get("/operational-summary", response_model=OperationalSummaryResponse)
def get_operational_summary(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    validate_date_range(start_date, end_date)
    return operational_summary(db, start_date=start_date, end_date=end_date)


@router.get("/fuel-efficiency", response_model=FuelEfficiencyResponse)
def get_fuel_efficiency(
    vehicle_id: UUID | None = None,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_fleet_analytics),
):
    validate_date_range(start_date, end_date)
    return fuel_efficiency(db, vehicle_id=vehicle_id, start_date=start_date, end_date=end_date)


@router.get("/fuel-cost-trends", response_model=FuelCostTrendsResponse)
def get_fuel_cost_trends(
    vehicle_id: UUID | None = None,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_fleet_analytics),
):
    validate_date_range(start_date, end_date)
    return fuel_cost_trends(db, vehicle_id=vehicle_id, start_date=start_date, end_date=end_date)
