from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.trip import Trip
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment
from app.core.deps import get_current_user


router = APIRouter(
    prefix="/trips",
    tags=["Trips"],
)


# =========================================================
# SCHEMAS
# =========================================================

class TripCreate(BaseModel):
    vehicle_id: UUID
    driver_id: UUID
    shipment_id: UUID

    start_location: str
    destination: str

    start_time: datetime | None = None
    end_time: datetime | None = None

    distance: float | None = None


class TripUpdate(BaseModel):
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    shipment_id: UUID | None = None

    start_location: str | None = None
    destination: str | None = None

    start_time: datetime | None = None
    end_time: datetime | None = None

    distance: float | None = None
    status: str | None = None


class TripOut(BaseModel):
    trip_id: UUID

    vehicle_id: UUID
    driver_id: UUID
    shipment_id: UUID

    start_location: str | None
    destination: str | None

    start_time: datetime | None
    end_time: datetime | None

    distance: float | None
    status: str | None

    class Config:
        from_attributes = True


# =========================================================
# GET ALL TRIPS
# =========================================================

@router.get(
    "/",
    response_model=list[TripOut],
)
def get_trips(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return all trips that have valid vehicle,
    driver and shipment references.
    """

    return (
        db.query(Trip)
        .filter(
            Trip.vehicle_id.is_not(None),
            Trip.driver_id.is_not(None),
            Trip.shipment_id.is_not(None),
        )
        .all()
    )


# =========================================================
# CREATE TRIP
# =========================================================

@router.post(
    "/",
    response_model=TripOut,
    status_code=status.HTTP_201_CREATED,
)
def create_trip(
    trip_data: TripCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # -----------------------------------------------------
    # Check vehicle
    # -----------------------------------------------------

    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.vehicle_id == trip_data.vehicle_id
        )
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    # -----------------------------------------------------
    # Check driver
    # -----------------------------------------------------

    driver = (
        db.query(Driver)
        .filter(
            Driver.driver_id == trip_data.driver_id
        )
        .first()
    )

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver not found",
        )

    # -----------------------------------------------------
    # Check shipment
    # -----------------------------------------------------

    shipment = (
        db.query(Shipment)
        .filter(
            Shipment.shipment_id
            == trip_data.shipment_id
        )
        .first()
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    # -----------------------------------------------------
    # Create trip
    # -----------------------------------------------------

    trip = Trip(
        vehicle_id=trip_data.vehicle_id,
        driver_id=trip_data.driver_id,
        shipment_id=trip_data.shipment_id,

        start_location=trip_data.start_location,
        destination=trip_data.destination,

        start_time=trip_data.start_time,
        end_time=trip_data.end_time,

        distance=trip_data.distance,

        status="Scheduled",
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return trip


# =========================================================
# GET SINGLE TRIP
# =========================================================

@router.get(
    "/{trip_id}",
    response_model=TripOut,
)
def get_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    trip = (
        db.query(Trip)
        .filter(
            Trip.trip_id == trip_id
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return trip


# =========================================================
# UPDATE TRIP
# =========================================================

@router.put(
    "/{trip_id}",
    response_model=TripOut,
)
def update_trip(
    trip_id: UUID,
    trip_data: TripUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # -----------------------------------------------------
    # Find trip
    # -----------------------------------------------------

    trip = (
        db.query(Trip)
        .filter(
            Trip.trip_id == trip_id
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    update_data = trip_data.model_dump(
        exclude_unset=True
    )

    # -----------------------------------------------------
    # Validate vehicle if being changed
    # -----------------------------------------------------

    if "vehicle_id" in update_data:
        vehicle = (
            db.query(Vehicle)
            .filter(
                Vehicle.vehicle_id
                == update_data["vehicle_id"]
            )
            .first()
        )

        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found",
            )

    # -----------------------------------------------------
    # Validate driver if being changed
    # -----------------------------------------------------

    if "driver_id" in update_data:
        driver = (
            db.query(Driver)
            .filter(
                Driver.driver_id
                == update_data["driver_id"]
            )
            .first()
        )

        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Driver not found",
            )

    # -----------------------------------------------------
    # Validate shipment if being changed
    # -----------------------------------------------------

    if "shipment_id" in update_data:
        shipment = (
            db.query(Shipment)
            .filter(
                Shipment.shipment_id
                == update_data["shipment_id"]
            )
            .first()
        )

        if not shipment:
            raise HTTPException(
                status_code=404,
                detail="Shipment not found",
            )

    # -----------------------------------------------------
    # Validate distance
    # -----------------------------------------------------

    if "distance" in update_data:
        distance = update_data["distance"]

        if distance is not None and distance < 0:
            raise HTTPException(
                status_code=400,
                detail="Distance cannot be negative",
            )

    # -----------------------------------------------------
    # Update fields
    # -----------------------------------------------------

    for field, value in update_data.items():
        setattr(
            trip,
            field,
            value,
        )

    db.commit()
    db.refresh(trip)

    return trip


# =========================================================
# DELETE TRIP
# =========================================================

@router.delete(
    "/{trip_id}",
)
def delete_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # -----------------------------------------------------
    # Find trip
    # -----------------------------------------------------

    trip = (
        db.query(Trip)
        .filter(
            Trip.trip_id == trip_id
        )
        .first()
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    db.delete(trip)
    db.commit()

    return {
        "message": "Trip deleted successfully"
    }