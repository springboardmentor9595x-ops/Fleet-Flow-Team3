from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.routing import route_remaining_metrics
from app.models.attendance import Attendance, AttendanceActivityType
from app.models.driver import Driver
from app.models.gps_tracking import GPSTracking
from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip, TripStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.trip import TripCreate, TripEnd, TripUpdate


def get_trip(db: Session, trip_id: UUID) -> Trip | None:
    return db.query(Trip).filter(Trip.trip_id == trip_id).first()


def get_trips_for_user(db: Session, current_user) -> list[Trip]:
    query = db.query(Trip)
    if current_user.role.value == "Driver":
        query = query.join(Driver, Trip.driver_id == Driver.driver_id).filter(Driver.user_id == current_user.user_id)
    return query.order_by(Trip.created_at.desc()).all()


def is_driver_assigned_to_trip(db: Session, trip: Trip, user_id: UUID) -> bool:
    return db.query(Driver).filter(Driver.driver_id == trip.driver_id, Driver.user_id == user_id).first() is not None


def has_other_committed_trip(
    db: Session,
    *,
    vehicle_id: UUID,
    driver_id: UUID,
    excluded_trip_id: UUID | None = None,
) -> bool:
    """A Scheduled or Active trip reserves both its vehicle and driver."""
    query = db.query(Trip).filter(
        Trip.status.in_([TripStatus.Scheduled, TripStatus.Active])
    )
    if excluded_trip_id:
        query = query.filter(Trip.trip_id != excluded_trip_id)
    return query.filter((Trip.vehicle_id == vehicle_id) | (Trip.driver_id == driver_id)).first() is not None


def get_trip_dependencies(db: Session, shipment_id: UUID, vehicle_id: UUID, driver_id: UUID):
    return (
        db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first(),
        db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first(),
        db.query(Driver).filter(Driver.driver_id == driver_id).first(),
    )


def create_trip(db: Session, trip_data: TripCreate) -> Trip:
    values = trip_data.model_dump()
    # Scheduling only reserves the trip resources. An Admin must explicitly
    # calculate and save route values before the trip can start.
    values["planned_distance"] = None
    values["estimated_duration"] = None
    values["eta"] = None
    trip = Trip(**values)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip(db: Session, trip: Trip, trip_data: TripUpdate) -> Trip:
    values = trip_data.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(trip, field, value)
    if {"source", "destination", "route_type"}.intersection(values):
        # A changed route input invalidates the previously calculated OSRM route.
        # The existing POST /trips/{trip_id}/route endpoint then recalculates it.
        trip.route_geometry = None
        trip.planned_distance = None
        trip.estimated_duration = None
        trip.eta = None
    db.commit()
    db.refresh(trip)
    return trip


def save_route(db: Session, trip: Trip, route_data: dict, route_type: str) -> Trip:
    trip.route_type = route_type
    trip.planned_distance = route_data["distance_meters"]
    trip.estimated_duration = route_data["duration_seconds"]
    trip.eta = datetime.now(timezone.utc) + timedelta(seconds=route_data["duration_seconds"])
    trip.route_geometry = route_data["geometry"]
    db.commit()
    db.refresh(trip)
    return trip


def get_route_metrics(
    db: Session,
    trip: Trip,
    current_location: GPSTracking | None = None,
) -> dict:
    """Return the current ETA and remaining route values for a trip."""
    remaining_distance = trip.planned_distance
    remaining_duration = trip.estimated_duration

    if current_location is None and trip.status == TripStatus.Active:
        current_location = (
            db.query(GPSTracking)
            .filter(GPSTracking.vehicle_id == trip.vehicle_id)
            .order_by(GPSTracking.recorded_time.desc())
            .first()
        )

    if current_location is not None:
        remaining_distance, remaining_duration = route_remaining_metrics(
            trip.route_geometry,
            current_location.latitude,
            current_location.longitude,
            trip.planned_distance,
            trip.estimated_duration,
        )

    eta = trip.eta
    if trip.status == TripStatus.Active and remaining_duration is not None:
        eta = datetime.now(timezone.utc) + timedelta(seconds=remaining_duration)

    return {
        "remaining_distance": remaining_distance,
        "remaining_duration": remaining_duration,
        "eta": eta,
    }


def update_active_trip_eta(
    db: Session,
    vehicle_id: UUID,
    current_location: GPSTracking,
) -> dict | None:
    """Persist the ETA recalculated for an active trip after a GPS update."""
    trip = (
        db.query(Trip)
        .filter(Trip.vehicle_id == vehicle_id, Trip.status == TripStatus.Active)
        .first()
    )
    if trip is None or not trip.route_geometry:
        return None

    metrics = get_route_metrics(db, trip, current_location)
    trip.eta = metrics["eta"]
    db.commit()
    db.refresh(trip)
    return {
        "trip_id": str(trip.trip_id),
        "remaining_distance": metrics["remaining_distance"],
        "remaining_duration": metrics["remaining_duration"],
        "eta": trip.eta.isoformat() if trip.eta else None,
    }


def start_trip(db: Session, trip: Trip, vehicle: Vehicle, shipment: Shipment) -> Trip:
    trip.status = TripStatus.Active
    trip.started_at = datetime.now(timezone.utc)
    if trip.eta is None and trip.estimated_duration is not None:
        trip.eta = trip.started_at + timedelta(seconds=trip.estimated_duration)
    vehicle.status = VehicleStatus.InTransit
    vehicle.assigned_driver = trip.driver_id
    if shipment.status == ShipmentStatus.Assigned:
        shipment.status = ShipmentStatus.InTransit
    driver = db.query(Driver).filter(Driver.driver_id == trip.driver_id).first()
    if driver and getattr(driver.status, "value", driver.status) != "Inactive":
        driver.status = "On Trip"
    db.add(
        Attendance(
            driver_id=trip.driver_id,
            trip_id=trip.trip_id,
            activity_type=AttendanceActivityType.TripStarted,
            notes="Trip started",
        )
    )
    db.commit()
    db.refresh(trip)
    return trip


def end_trip(db: Session, trip: Trip, vehicle: Vehicle, shipment: Shipment, end_data: TripEnd) -> Trip:
    trip.status = TripStatus.Completed
    trip.ended_at = datetime.now(timezone.utc)
    trip.actual_distance_meters = (
        end_data.actual_distance_meters
        if end_data.actual_distance_meters is not None
        else trip.planned_distance
    )
    vehicle.status = VehicleStatus.Available
    vehicle.assigned_driver = None
    if shipment.status == ShipmentStatus.InTransit:
        shipment.status = ShipmentStatus.Delivered
    driver = db.query(Driver).filter(Driver.driver_id == trip.driver_id).first()
    if driver and getattr(driver.status, "value", driver.status) != "Inactive":
        driver.status = "Available"
    db.add(
        Attendance(
            driver_id=trip.driver_id,
            trip_id=trip.trip_id,
            activity_type=AttendanceActivityType.TripCompleted,
            notes="Trip completed",
        )
    )
    db.commit()
    db.refresh(trip)
    return trip


def delete_scheduled_trip(db: Session, trip: Trip) -> None:
    """Delete an unstarted trip and release its reserved vehicle."""
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == trip.vehicle_id).first()
    if vehicle:
        vehicle.status = VehicleStatus.Available
        vehicle.assigned_driver = None
    driver = db.query(Driver).filter(Driver.driver_id == trip.driver_id).first()
    if driver and getattr(driver.status, "value", driver.status) != "Inactive":
        other_trip = (
            db.query(Trip)
            .filter(
                Trip.driver_id == trip.driver_id,
                Trip.status.in_([TripStatus.Scheduled, TripStatus.Active]),
                Trip.trip_id != trip.trip_id,
            )
            .first()
        )
        if other_trip is None:
            driver.status = "Available"
    db.delete(trip)
    db.commit()


def has_active_trip_for_vehicle(db: Session, vehicle_id: UUID) -> bool:
    return (
        db.query(Trip)
        .filter(Trip.vehicle_id == vehicle_id, Trip.status == TripStatus.Active)
        .first()
        is not None
    )
