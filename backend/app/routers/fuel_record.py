from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin_or_fleet_manager, role_value
from app.crud.driver import get_assigned_vehicle, get_driver_by_user_id
from app.crud.fuel_record import (
    create_fuel_record,
    delete_fuel_record,
    get_fuel_record,
    get_fuel_records,
    update_fuel_record,
)
from app.crud.vehicle import get_vehicle_by_id
from app.schemas.fuel_record import FuelRecordCreate, FuelRecordResponse, FuelRecordUpdate
from database import get_db


router = APIRouter(prefix="/fuel-records", tags=["Fuel Records"])


def ensure_vehicle_exists(db: Session, vehicle_id: UUID) -> None:
    if get_vehicle_by_id(db, vehicle_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")


def assigned_vehicle_for_driver(db: Session, current_user):
    """Resolve a Driver's vehicle from the server-side assignment, never a request parameter."""
    driver_row = get_driver_by_user_id(db, current_user.user_id)
    driver = driver_row[0] if driver_row else None
    return get_assigned_vehicle(db, driver.driver_id) if driver else None


def driver_can_read_record(db: Session, current_user, record) -> None:
    if role_value(current_user) != "Driver":
        return
    vehicle = assigned_vehicle_for_driver(db, current_user)
    if vehicle is None or record.vehicle_id != vehicle.vehicle_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Drivers can view fuel records only for their assigned vehicle.")


@router.post("/", response_model=FuelRecordResponse, status_code=status.HTTP_201_CREATED)
def add_fuel_record(
    payload: FuelRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager),
):
    ensure_vehicle_exists(db, payload.vehicle_id)
    return create_fuel_record(db, payload)


@router.get("/", response_model=list[FuelRecordResponse])
def list_fuel_records(
    vehicle_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if role_value(current_user) == "Driver":
        vehicle = assigned_vehicle_for_driver(db, current_user)
        return [] if vehicle is None else get_fuel_records(db, vehicle_id=vehicle.vehicle_id)
    if role_value(current_user) not in {"Admin", "FleetManager", "Dispatcher"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to view fuel records.")
    return get_fuel_records(db, vehicle_id=vehicle_id)


@router.get("/{fuel_id}", response_model=FuelRecordResponse)
def get_single_fuel_record(
    fuel_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    record = get_fuel_record(db, fuel_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel record not found")
    driver_can_read_record(db, current_user, record)
    if role_value(current_user) not in {"Admin", "FleetManager", "Dispatcher", "Driver"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to view fuel records.")
    return record


@router.put("/{fuel_id}", response_model=FuelRecordResponse)
def edit_fuel_record(
    fuel_id: UUID,
    payload: FuelRecordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager),
):
    record = get_fuel_record(db, fuel_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel record not found")
    if payload.vehicle_id is not None:
        ensure_vehicle_exists(db, payload.vehicle_id)
    return update_fuel_record(db, record, payload)


@router.delete("/{fuel_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_fuel_record(
    fuel_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager),
):
    record = get_fuel_record(db, fuel_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel record not found")
    delete_fuel_record(db, record)
