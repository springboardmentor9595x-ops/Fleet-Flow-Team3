from sqlalchemy import func

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from app.models.vehicle import Vehicle
from app.core.deps import require_fleet_analytics
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.crud.maintenance import get_upcoming_and_overdue

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/fleet")
def fleet_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_fleet_analytics)
):
    vehicle_query = db.query(Vehicle)

    total = vehicle_query.count()

    available = vehicle_query.filter(
        Vehicle.status == VehicleStatus.Available
    ).count()

    assigned = vehicle_query.filter(
        Vehicle.status == VehicleStatus.Assigned
    ).count()

    maintenance = vehicle_query.filter(
        Vehicle.status == VehicleStatus.Maintenance
    ).count()

    in_transit = vehicle_query.filter(
        Vehicle.status == VehicleStatus.InTransit
    ).count()

    upcoming, overdue = get_upcoming_and_overdue(db)
    maintenance_cost = db.query(func.coalesce(func.sum(Maintenance.cost), 0)).filter(
        Maintenance.status.in_([MaintenanceStatus.Completed, MaintenanceStatus.Resolved])
    ).scalar()

    return {
        "total_vehicles": total,
        "available": available,
        "assigned": assigned,
        "maintenance": maintenance,
        "in_transit": in_transit,
        "upcoming_services": len(upcoming),
        "overdue_services": len(overdue),
        "maintenance_cost_summary": float(maintenance_cost or 0),
    }
