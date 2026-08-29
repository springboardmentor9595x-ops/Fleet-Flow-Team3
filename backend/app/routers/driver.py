from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin_or_fleet_manager
from app.crud.driver import (
    assign_driver_to_vehicle, create_driver, delete_driver, driver_has_active_trip,
    driver_has_committed_trip, driver_has_trip_history, get_all_drivers,
    get_assigned_vehicle, get_current_trip, get_driver, get_driver_by_license_number,
    get_driver_by_user_id, reassign_driver_to_vehicle, unassign_driver_from_vehicle,
    update_driver, vehicle_has_committed_trip,
)
from app.crud.vehicle import get_vehicle_by_id
from app.models.user import RoleEnum, User
from app.models.vehicle import VehicleStatus
from app.schemas.driver import (
    AssignedVehicleResponse, CurrentTripResponse, DriverCreate, DriverResponse, DriverUpdate,
)
from app.services.notification import create_notification
from database import get_db


router = APIRouter(prefix="/drivers", tags=["Drivers"])


def value_of(value):
    return value.value if hasattr(value, "value") else value


def driver_response(db: Session, driver) -> DriverResponse:
    user = db.query(User).filter(User.user_id == driver.user_id).first() if driver.user_id else None
    vehicle = get_assigned_vehicle(db, driver.driver_id)
    trip = get_current_trip(db, driver.driver_id)
    return DriverResponse(
        driver_id=driver.driver_id, full_name=driver.full_name, user_id=driver.user_id,
        email=user.email if user else None, phone=user.phone if user else None,
        license_number=driver.license_number, experience_years=driver.experience_years or 0,
        address=driver.address, status=value_of(driver.status),
        assigned_vehicle_id=vehicle.vehicle_id if vehicle else None,
        assigned_vehicle=(AssignedVehicleResponse(vehicle_id=vehicle.vehicle_id, registration_number=vehicle.registration_number, status=value_of(vehicle.status)) if vehicle else None),
        current_trip=(CurrentTripResponse(trip_id=trip.trip_id, source=trip.source, destination=trip.destination, status=value_of(trip.status), started_at=trip.started_at) if trip else None),
    )


def linked_driver_user_or_error(db: Session, user_id: UUID) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked user not found.")
    if user.role != RoleEnum.Driver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The linked user must have the Driver role.")
    return user


def validate_license_number(db: Session, license_number: str | None, current_driver_id: UUID | None = None) -> None:
    if not license_number:
        return
    existing = get_driver_by_license_number(db, license_number)
    if existing and existing.driver_id != current_driver_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This license number is already registered.")


def validate_assignment_state(db: Session, driver, vehicle) -> None:
    if value_of(driver.status) == "Inactive":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An inactive driver cannot be assigned to a vehicle.")
    if vehicle.status == VehicleStatus.Maintenance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A vehicle in Maintenance cannot receive a driver assignment.")
    if vehicle.status != VehicleStatus.Available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only an available vehicle can receive a permanent driver assignment.")
    if vehicle.assigned_driver and vehicle.assigned_driver != driver.driver_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This vehicle is already assigned to another driver.")
    if driver_has_committed_trip(db, driver.driver_id) or vehicle_has_committed_trip(db, vehicle.vehicle_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A driver or vehicle reserved for a scheduled or active trip cannot be reassigned.")


def notify_driver_vehicle_change(db: Session, driver, vehicle, action: str) -> None:
    if driver.user_id is None:
        return
    messages = {
        "assigned": ("Vehicle Assigned", f"Vehicle {vehicle.registration_number} has been assigned to you."),
        "reassigned": ("Vehicle Assignment Updated", f"Vehicle {vehicle.registration_number} has been assigned to you."),
        "unassigned": ("Vehicle Unassigned", f"Vehicle {vehicle.registration_number} is no longer assigned to you."),
    }
    title, message = messages[action]
    create_notification(
        db,
        user_id=driver.user_id,
        title=title,
        message=message,
        notification_type="driver_assignment",
        alert_type=f"driver_assignment:{action}:{driver.driver_id}:{vehicle.vehicle_id}",
    )


@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_new_driver(driver_data: DriverCreate, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    linked_driver_user_or_error(db, driver_data.user_id)
    if get_driver_by_user_id(db, driver_data.user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user is already linked to a driver.")
    validate_license_number(db, driver_data.license_number)
    return driver_response(db, create_driver(db, driver_data))


@router.get("/", response_model=list[DriverResponse])
def list_drivers(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return [driver_response(db, driver) for driver, _ in get_all_drivers(db)]
    if current_user.role.value == "Driver":
        own_driver = get_driver_by_user_id(db, current_user.user_id)
        return [driver_response(db, own_driver[0])] if own_driver else []
    return []


@router.post("/{driver_id}/assign-vehicle/{vehicle_id}", response_model=DriverResponse)
def assign_vehicle(driver_id: UUID, vehicle_id: UUID, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    driver, vehicle = get_driver(db, driver_id), get_vehicle_by_id(db, vehicle_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    if get_assigned_vehicle(db, driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver already has a vehicle assignment. Use reassign or unassign first.")
    validate_assignment_state(db, driver, vehicle)
    assign_driver_to_vehicle(db, driver, vehicle)
    notify_driver_vehicle_change(db, driver, vehicle, "assigned")
    return driver_response(db, driver)


@router.post("/{driver_id}/reassign-vehicle/{vehicle_id}", response_model=DriverResponse)
def reassign_vehicle(driver_id: UUID, vehicle_id: UUID, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    driver, vehicle = get_driver(db, driver_id), get_vehicle_by_id(db, vehicle_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    previous_vehicle = get_assigned_vehicle(db, driver_id)
    if previous_vehicle and previous_vehicle.vehicle_id == vehicle.vehicle_id:
        return driver_response(db, driver)
    if previous_vehicle and vehicle_has_committed_trip(db, previous_vehicle.vehicle_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The current vehicle is reserved for a scheduled or active trip and cannot be reassigned.")
    validate_assignment_state(db, driver, vehicle)
    reassign_driver_to_vehicle(db, driver, previous_vehicle, vehicle)
    notify_driver_vehicle_change(db, driver, vehicle, "reassigned")
    return driver_response(db, driver)


@router.delete("/{driver_id}/unassign-vehicle", response_model=DriverResponse)
def unassign_vehicle(driver_id: UUID, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    driver = get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    vehicle = get_assigned_vehicle(db, driver_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver does not have a vehicle assignment.")
    if driver_has_committed_trip(db, driver_id) or vehicle_has_committed_trip(db, vehicle.vehicle_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A driver or vehicle reserved for a scheduled or active trip cannot be unassigned.")
    unassign_driver_from_vehicle(db, vehicle)
    notify_driver_vehicle_change(db, driver, vehicle, "unassigned")
    return driver_response(db, driver)


@router.get("/{driver_id}", response_model=DriverResponse)
def get_single_driver(driver_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    driver = get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return driver_response(db, driver)
    if current_user.role.value == "Driver" and driver.user_id == current_user.user_id:
        return driver_response(db, driver)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this driver.")


@router.put("/{driver_id}", response_model=DriverResponse)
def update_existing_driver(driver_id: UUID, driver_data: DriverUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    driver = get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    changes = driver_data.model_dump(exclude_unset=True)
    if "user_id" in changes:
        if changes["user_id"] is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A driver profile must remain linked to a Driver user.")
        if changes["user_id"] != driver.user_id:
            linked_driver_user_or_error(db, changes["user_id"])
            if get_driver_by_user_id(db, changes["user_id"]):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This user is already linked to a driver.")
    if "license_number" in changes:
        validate_license_number(db, changes["license_number"], driver.driver_id)
    return driver_response(db, update_driver(db, driver, driver_data))


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_driver(driver_id: UUID, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    driver = get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    if driver_has_active_trip(db, driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A driver assigned to an active trip cannot be deleted.")
    if driver_has_trip_history(db, driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A driver with trip history cannot be deleted.")
    if get_assigned_vehicle(db, driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unassign the driver from the vehicle before deletion.")
    delete_driver(db, driver)
