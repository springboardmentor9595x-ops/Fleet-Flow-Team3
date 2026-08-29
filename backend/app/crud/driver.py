from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.trip import Trip, TripStatus
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.driver import DriverCreate, DriverUpdate


def get_all_drivers(db: Session):
    return (
        db.query(Driver, User)
        .outerjoin(User, Driver.user_id == User.user_id)
        .order_by(Driver.full_name.asc(), Driver.driver_id.asc())
        .all()
    )


def get_driver_by_user_id(db: Session, user_id):
    return (
        db.query(Driver, User)
        .outerjoin(User, Driver.user_id == User.user_id)
        .filter(Driver.user_id == user_id)
        .first()
    )


def get_driver(db: Session, driver_id):
    return db.query(Driver).filter(Driver.driver_id == driver_id).first()


def get_driver_by_license_number(db: Session, license_number: str):
    return db.query(Driver).filter(Driver.license_number == license_number).first()


def create_driver(db: Session, driver_data: DriverCreate) -> Driver:
    driver = Driver(**driver_data.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


def update_driver(db: Session, driver: Driver, driver_data: DriverUpdate) -> Driver:
    for field, value in driver_data.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver


def driver_has_active_trip(db: Session, driver_id) -> bool:
    return (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id, Trip.status == TripStatus.Active)
        .first()
        is not None
    )


def driver_has_trip_history(db: Session, driver_id) -> bool:
    return db.query(Trip).filter(Trip.driver_id == driver_id).first() is not None


def driver_has_committed_trip(db: Session, driver_id) -> bool:
    return (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id, Trip.status.in_([TripStatus.Scheduled, TripStatus.Active]))
        .first()
        is not None
    )


def vehicle_has_committed_trip(db: Session, vehicle_id) -> bool:
    return (
        db.query(Trip)
        .filter(Trip.vehicle_id == vehicle_id, Trip.status.in_([TripStatus.Scheduled, TripStatus.Active]))
        .first()
        is not None
    )


def get_assigned_vehicle(db: Session, driver_id):
    return db.query(Vehicle).filter(Vehicle.assigned_driver == driver_id).first()


def get_current_trip(db: Session, driver_id):
    return (
        db.query(Trip)
        .filter(Trip.driver_id == driver_id, Trip.status.in_([TripStatus.Scheduled, TripStatus.Active]))
        .order_by(Trip.created_at.desc())
        .first()
    )


def assign_driver_to_vehicle(db: Session, driver: Driver, vehicle: Vehicle) -> None:
    vehicle.assigned_driver = driver.driver_id
    db.commit()
    db.refresh(vehicle)


def reassign_driver_to_vehicle(db: Session, driver: Driver, previous_vehicle: Vehicle | None, new_vehicle: Vehicle) -> None:
    if previous_vehicle and previous_vehicle.vehicle_id != new_vehicle.vehicle_id:
        previous_vehicle.assigned_driver = None
    new_vehicle.assigned_driver = driver.driver_id
    db.commit()
    db.refresh(new_vehicle)


def unassign_driver_from_vehicle(db: Session, vehicle: Vehicle) -> None:
    vehicle.assigned_driver = None
    db.commit()
    db.refresh(vehicle)


def delete_driver(db: Session, driver: Driver) -> None:
    db.delete(driver)
    db.commit()
