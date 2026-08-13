from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


# --------------------------------
# CREATE VEHICLE
# --------------------------------

def create_vehicle(
    db: Session,
    vehicle_data: VehicleCreate
):
    vehicle = Vehicle(
        registration_number=vehicle_data.registration_number,
        vehicle_type=vehicle_data.vehicle_type,
        brand=vehicle_data.brand,
        model=vehicle_data.model,
        manufacture_year=vehicle_data.manufacture_year,
        fuel_type=vehicle_data.fuel_type,
        capacity=vehicle_data.capacity,
        driver_id=vehicle_data.driver_id,
        status=vehicle_data.status,
    )

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle


# --------------------------------
# GET ALL VEHICLES
# --------------------------------

def get_all_vehicles(
    db: Session
):
    return db.query(Vehicle).all()


# --------------------------------
# GET VEHICLE BY ID
# --------------------------------

def get_vehicle_by_id(
    db: Session,
    vehicle_id
):
    return (
        db.query(Vehicle)
        .filter(Vehicle.vehicle_id == vehicle_id)
        .first()
    )


# --------------------------------
# UPDATE VEHICLE
# --------------------------------

def update_vehicle(
    db: Session,
    vehicle,
    vehicle_data: VehicleUpdate
):

    update_data = vehicle_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    return vehicle


# --------------------------------
# DELETE VEHICLE
# --------------------------------

def delete_vehicle(
    db: Session,
    vehicle
):

    db.delete(vehicle)
    db.commit()

    return True