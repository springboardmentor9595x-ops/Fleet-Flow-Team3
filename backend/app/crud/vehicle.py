from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.models.trip import Trip, TripStatus
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def create_vehicle(db: Session, vehicle: VehicleCreate):
    """
    Register a new vehicle.
    """

    db_vehicle = Vehicle(
        registration_number=vehicle.registration_number,
        vehicle_type=vehicle.vehicle_type,
        brand=vehicle.brand,
        model=vehicle.model,
        manufacture_year=vehicle.manufacture_year,
        fuel_type=vehicle.fuel_type,
        capacity=vehicle.capacity,
    )

    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)

    return db_vehicle


def get_all_vehicles(db: Session):
    """
    Get all vehicles.
    """

    return db.query(Vehicle).all()


def get_vehicle_by_id(db: Session, vehicle_id):
    """
    Get one vehicle.
    """

    return (
        db.query(Vehicle)
        .filter(Vehicle.vehicle_id == vehicle_id)
        .first()
    )


def update_vehicle(db: Session, vehicle_id, vehicle_data: VehicleUpdate):
    """
    Update vehicle details.
    """

    vehicle = get_vehicle_by_id(db, vehicle_id)

    if not vehicle:
        return None

    for key, value in vehicle_data.model_dump().items():
        setattr(vehicle, key, value)

    db.commit()
    db.refresh(vehicle)

    return vehicle


def delete_vehicle(db: Session, vehicle_id):
    """
    Delete a vehicle.
    """

    vehicle = get_vehicle_by_id(db, vehicle_id)

    if not vehicle:
        return None

    db.delete(vehicle)
    db.commit()

    return vehicle


def vehicle_has_active_trip(db: Session, vehicle_id) -> bool:
    return (
        db.query(Trip)
        .filter(Trip.vehicle_id == vehicle_id, Trip.status == TripStatus.Active)
        .first()
        is not None
    )


def vehicle_has_trip_history(db: Session, vehicle_id) -> bool:
    return db.query(Trip).filter(Trip.vehicle_id == vehicle_id).first() is not None
