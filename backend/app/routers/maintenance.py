from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.maintenance import VehicleMaintenance
from app.models.vehicle import Vehicle
from app.core.deps import get_current_user, require_roles
from app.models.user import RoleEnum


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"],
)


# --------------------------------
# Pydantic Schemas
# --------------------------------

class MaintenanceCreate(BaseModel):
    vehicle_id: UUID
    maintenance_type: str = "General Inspection"
    service_date: datetime | None = None
    next_service_date: datetime | None = None
    cost: float = 0.0
    remarks: str | None = None
    performed_by: str | None = None


class MaintenanceUpdate(BaseModel):
    maintenance_type: str | None = None
    service_date: datetime | None = None
    next_service_date: datetime | None = None
    cost: float | None = None
    remarks: str | None = None
    status: str | None = None
    performed_by: str | None = None


class MaintenanceOut(BaseModel):
    maintenance_id: UUID
    vehicle_id: UUID | None = None
    maintenance_type: str | None = None
    service_date: datetime | None = None
    next_service_date: datetime | None = None
    cost: float | None = None
    remarks: str | None = None
    status: str | None = None
    performed_by: str | None = None

    class Config:
        from_attributes = True


# =========================================================
# GET ALL MAINTENANCE RECORDS
# Admin / FleetManager / Dispatcher: all
# Driver: only records for their assigned vehicle
# =========================================================

@router.get(
    "/",
    response_model=list[MaintenanceOut],
)
def get_maintenance_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Driver sees only their assigned vehicle's maintenance
    if current_user.role == RoleEnum.Driver or str(current_user.role) == "Driver":
        from app.models.driver import Driver
        driver_profile = (
            db.query(Driver)
            .filter(Driver.user_id == current_user.user_id)
            .first()
        )
        if not driver_profile or not driver_profile.vehicles:
            return []
        vehicle_ids = [v.vehicle_id for v in driver_profile.vehicles]
        return (
            db.query(VehicleMaintenance)
            .filter(VehicleMaintenance.vehicle_id.in_(vehicle_ids))
            .order_by(VehicleMaintenance.service_date.desc())
            .all()
        )

    return db.query(VehicleMaintenance).order_by(VehicleMaintenance.service_date.desc()).all()


# =========================================================
# MAINTENANCE ALERTS — MUST be before /{maintenance_id}
# Returns upcoming (within 7 days) and overdue records
# Admin / FleetManager / Dispatcher
# =========================================================

@router.get(
    "/alerts",
)
def get_maintenance_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from datetime import timedelta
    now = datetime.utcnow()
    seven_days = now + timedelta(days=7)

    # Driver: only their assigned vehicle
    if current_user.role == RoleEnum.Driver or str(current_user.role) == "Driver":
        from app.models.driver import Driver
        driver_profile = (
            db.query(Driver)
            .filter(Driver.user_id == current_user.user_id)
            .first()
        )
        if not driver_profile or not driver_profile.vehicles:
            return {"total_alerts": 0, "alerts": []}
        vehicle_ids = [v.vehicle_id for v in driver_profile.vehicles]
        base_query = (
            db.query(VehicleMaintenance)
            .filter(VehicleMaintenance.vehicle_id.in_(vehicle_ids))
        )
    else:
        base_query = db.query(VehicleMaintenance)

    records = (
        base_query
        .filter(
            VehicleMaintenance.status != "Completed",
            VehicleMaintenance.next_service_date.isnot(None),
            VehicleMaintenance.next_service_date <= seven_days,
        )
        .order_by(VehicleMaintenance.next_service_date.asc())
        .all()
    )

    result = []
    for record in records:
        alert_level = (
            "overdue"
            if record.next_service_date < now
            else "upcoming"
        )
        result.append({
            "maintenance_id": record.maintenance_id,
            "vehicle_id": record.vehicle_id,
            "maintenance_type": record.maintenance_type,
            "next_service_date": record.next_service_date,
            "status": record.status,
            "alert_level": alert_level,
            "days_until_due": (record.next_service_date - now).days,
        })

    return {
        "total_alerts": len(result),
        "alerts": result,
    }


# =========================================================
# SCHEDULE MAINTENANCE
# Admin / FleetManager only
# =========================================================

@router.post(
    "/",
    response_model=MaintenanceOut,
    status_code=status.HTTP_201_CREATED,
)
def schedule_maintenance(
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(RoleEnum.Admin, RoleEnum.FleetManager)),
):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == maintenance_data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    maintenance = VehicleMaintenance(
        vehicle_id=maintenance_data.vehicle_id,
        maintenance_type=maintenance_data.maintenance_type,
        service_date=maintenance_data.service_date or datetime.utcnow(),
        next_service_date=maintenance_data.next_service_date,
        cost=maintenance_data.cost,
        remarks=maintenance_data.remarks,
        performed_by=maintenance_data.performed_by,
        status="Scheduled",
    )

    db.add(maintenance)
    vehicle.status = "Maintenance"

    db.commit()
    db.refresh(maintenance)

    return maintenance


# =========================================================
# GET SINGLE MAINTENANCE RECORD
# =========================================================

@router.get(
    "/{maintenance_id}",
    response_model=MaintenanceOut,
)
def get_maintenance(
    maintenance_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    maintenance = (
        db.query(VehicleMaintenance)
        .filter(VehicleMaintenance.maintenance_id == maintenance_id)
        .first()
    )

    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    return maintenance


# =========================================================
# UPDATE MAINTENANCE RECORD
# Admin / FleetManager only
# On Completed: auto-set vehicle status → Available
# =========================================================

@router.put(
    "/{maintenance_id}",
    response_model=MaintenanceOut,
)
def update_maintenance(
    maintenance_id: UUID,
    maintenance_data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(RoleEnum.Admin, RoleEnum.FleetManager)),
):
    maintenance = (
        db.query(VehicleMaintenance)
        .filter(VehicleMaintenance.maintenance_id == maintenance_id)
        .first()
    )

    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    for field, value in maintenance_data.dict(exclude_unset=True).items():
        setattr(maintenance, field, value)

    # Auto-restore vehicle status when maintenance completes
    if maintenance_data.status == "Completed" and maintenance.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == maintenance.vehicle_id).first()
        if vehicle:
            vehicle.status = "Available"

    db.commit()
    db.refresh(maintenance)

    return maintenance


# =========================================================
# DELETE MAINTENANCE RECORD
# Admin only
# =========================================================

@router.delete(
    "/{maintenance_id}",
)
def delete_maintenance(
    maintenance_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(RoleEnum.Admin)),
):
    maintenance = (
        db.query(VehicleMaintenance)
        .filter(VehicleMaintenance.maintenance_id == maintenance_id)
        .first()
    )

    if not maintenance:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    db.delete(maintenance)
    db.commit()

    return {"message": "Maintenance record deleted successfully"}