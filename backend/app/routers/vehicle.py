from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db

from app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse
)

from app.crud.vehicle import (
    create_vehicle,
    get_all_vehicles,
    get_vehicle_by_id,
    update_vehicle,
    delete_vehicle,
    vehicle_has_active_trip,
    vehicle_has_trip_history,
)

from app.core.deps import (
    get_current_user,
    require_admin_or_fleet_manager
)
from app.models.driver import Driver
from app.models.trip import Trip, TripStatus

router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


def driver_can_view_vehicle(db: Session, vehicle, current_user) -> bool:
    """Return whether a Driver owns the vehicle through an assignment/trip."""
    driver = db.query(Driver).filter(Driver.user_id == current_user.user_id).first()
    if driver is None:
        return False
    if vehicle.assigned_driver == driver.driver_id:
        return True
    return db.query(Trip).filter(
        Trip.driver_id == driver.driver_id,
        Trip.vehicle_id == vehicle.vehicle_id,
        Trip.status.in_([TripStatus.Scheduled, TripStatus.Active]),
    ).first() is not None


def require_vehicle_view_access(db: Session, vehicle, current_user) -> None:
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return
    if current_user.role.value == "Driver" and driver_can_view_vehicle(db, vehicle, current_user):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Drivers can view only their assigned vehicle.",
    )


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED
)
def register_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager)
):
    return create_vehicle(db, vehicle)


@router.get(
    "/",
    response_model=list[VehicleResponse]
)
def list_vehicles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    vehicles = get_all_vehicles(db)
    if current_user.role.value != "Driver":
        return vehicles
    return [vehicle for vehicle in vehicles if driver_can_view_vehicle(db, vehicle, current_user)]


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse
)
def get_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    vehicle = get_vehicle_by_id(db, vehicle_id)

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    require_vehicle_view_access(db, vehicle, current_user)
    return vehicle


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse
)
def edit_vehicle(
    vehicle_id: UUID,
    vehicle: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager)
):
    updated = update_vehicle(
        db,
        vehicle_id,
        vehicle
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    return updated


@router.delete(
    "/{vehicle_id}"
)
def remove_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager)
):
    if vehicle_has_active_trip(db, vehicle_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A vehicle assigned to an active trip cannot be deleted.",
        )
    if vehicle_has_trip_history(db, vehicle_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A vehicle with trip history cannot be deleted.",
        )
    deleted = delete_vehicle(
        db,
        vehicle_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    return {
        "message": "Vehicle deleted successfully"
    }
