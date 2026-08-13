from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.maintenance import VehicleMaintenance
from app.core.deps import get_current_user


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"],
)


# --------------------------------
# Schemas
# --------------------------------

class MaintenanceCreate(BaseModel):
    vehicle_id: UUID | None = None


class MaintenanceUpdate(BaseModel):
    vehicle_id: UUID | None = None


class MaintenanceOut(BaseModel):
    maintenance_id: UUID
    vehicle_id: UUID | None

    class Config:
        from_attributes = True


# --------------------------------
# GET ALL MAINTENANCE RECORDS
# --------------------------------

@router.get(
    "/",
    response_model=list[MaintenanceOut],
)
def get_maintenance_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(VehicleMaintenance).all()


# --------------------------------
# CREATE MAINTENANCE RECORD
# --------------------------------

@router.post(
    "/",
    response_model=MaintenanceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_maintenance(
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    maintenance = VehicleMaintenance(
        vehicle_id=maintenance_data.vehicle_id,
    )

    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)

    return maintenance


# --------------------------------
# GET SINGLE MAINTENANCE RECORD
# --------------------------------

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
        .filter(
            VehicleMaintenance.maintenance_id == maintenance_id
        )
        .first()
    )

    if not maintenance:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found",
        )

    return maintenance


# --------------------------------
# UPDATE MAINTENANCE RECORD
# --------------------------------

@router.put(
    "/{maintenance_id}",
    response_model=MaintenanceOut,
)
def update_maintenance(
    maintenance_id: UUID,
    maintenance_data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    maintenance = (
        db.query(VehicleMaintenance)
        .filter(
            VehicleMaintenance.maintenance_id == maintenance_id
        )
        .first()
    )

    if not maintenance:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found",
        )

    maintenance.vehicle_id = maintenance_data.vehicle_id

    db.commit()
    db.refresh(maintenance)

    return maintenance


# --------------------------------
# DELETE MAINTENANCE RECORD
# --------------------------------

@router.delete(
    "/{maintenance_id}",
)
def delete_maintenance(
    maintenance_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    maintenance = (
        db.query(VehicleMaintenance)
        .filter(
            VehicleMaintenance.maintenance_id == maintenance_id
        )
        .first()
    )

    if not maintenance:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found",
        )

    db.delete(maintenance)
    db.commit()

    return {
        "message": "Maintenance record deleted successfully"
    }