from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.fuel_record import FuelRecord
from app.core.deps import get_current_user


router = APIRouter(
    prefix="/fuel",
    tags=["Fuel Records"],
)


# --------------------------------
# Schemas
# --------------------------------

class FuelCreate(BaseModel):
    vehicle_id: UUID | None = None


class FuelUpdate(BaseModel):
    vehicle_id: UUID | None = None


class FuelOut(BaseModel):
    fuel_id: UUID
    vehicle_id: UUID | None

    class Config:
        from_attributes = True


# --------------------------------
# GET ALL FUEL RECORDS
# --------------------------------

@router.get(
    "/",
    response_model=list[FuelOut],
)
def get_fuel_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(FuelRecord).all()


# --------------------------------
# CREATE FUEL RECORD
# --------------------------------

@router.post(
    "/",
    response_model=FuelOut,
    status_code=status.HTTP_201_CREATED,
)
def create_fuel_record(
    fuel_data: FuelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fuel = FuelRecord(
        vehicle_id=fuel_data.vehicle_id,
    )

    db.add(fuel)
    db.commit()
    db.refresh(fuel)

    return fuel


# --------------------------------
# GET SINGLE FUEL RECORD
# --------------------------------

@router.get(
    "/{fuel_id}",
    response_model=FuelOut,
)
def get_fuel_record(
    fuel_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fuel = (
        db.query(FuelRecord)
        .filter(FuelRecord.fuel_id == fuel_id)
        .first()
    )

    if not fuel:
        raise HTTPException(
            status_code=404,
            detail="Fuel record not found",
        )

    return fuel


# --------------------------------
# UPDATE FUEL RECORD
# --------------------------------

@router.put(
    "/{fuel_id}",
    response_model=FuelOut,
)
def update_fuel_record(
    fuel_id: UUID,
    fuel_data: FuelUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fuel = (
        db.query(FuelRecord)
        .filter(FuelRecord.fuel_id == fuel_id)
        .first()
    )

    if not fuel:
        raise HTTPException(
            status_code=404,
            detail="Fuel record not found",
        )

    fuel.vehicle_id = fuel_data.vehicle_id

    db.commit()
    db.refresh(fuel)

    return fuel


# --------------------------------
# DELETE FUEL RECORD
# --------------------------------

@router.delete(
    "/{fuel_id}",
)
def delete_fuel_record(
    fuel_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fuel = (
        db.query(FuelRecord)
        .filter(FuelRecord.fuel_id == fuel_id)
        .first()
    )

    if not fuel:
        raise HTTPException(
            status_code=404,
            detail="Fuel record not found",
        )

    db.delete(fuel)
    db.commit()

    return {
        "message": "Fuel record deleted successfully"
    }