from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin_or_fleet_manager
from app.core.routing import build_route
from app.services.gps_simulator import gps_simulator
from app.crud.trip import (
    create_trip,
    delete_scheduled_trip,
    end_trip,
    get_trip,
    get_trip_dependencies,
    get_route_metrics,
    get_trips_for_user,
    has_other_committed_trip,
    is_driver_assigned_to_trip,
    save_route,
    start_trip,
    update_trip,
)
from app.models.shipment import ShipmentStatus
from app.models.driver import Driver, DriverStatus
from app.models.trip import Trip, TripStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.trip import RouteCalculationRequest, TripCreate, TripEnd, TripResponse, TripRouteResponse, TripUpdate
from app.services.notification import create_notification
from database import get_db


router = APIRouter(prefix="/trips", tags=["Trips"])


def get_dependencies_or_404(db: Session, shipment_id: UUID, vehicle_id: UUID, driver_id: UUID):
    shipment, vehicle, driver = get_trip_dependencies(db, shipment_id, vehicle_id, driver_id)
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return shipment, vehicle, driver


def require_trip_access(db: Session, trip, current_user) -> None:
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return
    if current_user.role.value == "Driver" and is_driver_assigned_to_trip(db, trip, current_user.user_id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this trip.")


def require_start_end_permission(db: Session, trip, current_user) -> None:
    if current_user.role.value in {"Admin", "FleetManager"}:
        return
    if current_user.role.value == "Driver" and is_driver_assigned_to_trip(db, trip, current_user.user_id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the assigned driver, an Admin, or a Fleet Manager can change this trip.")


def require_route_access(db: Session, trip, current_user) -> None:
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return
    if current_user.role.value == "Driver" and is_driver_assigned_to_trip(db, trip, current_user.user_id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to access this trip route.")


def route_response(db: Session, trip, fallback: bool = False) -> dict:
    metrics = get_route_metrics(db, trip)
    return {
        "trip_id": trip.trip_id,
        "route_type": trip.route_type,
        "planned_distance": trip.planned_distance,
        "estimated_duration": trip.estimated_duration,
        "eta": metrics["eta"],
        "remaining_distance": metrics["remaining_distance"],
        "remaining_duration": metrics["remaining_duration"],
        "geometry": trip.route_geometry,
        "fallback": fallback,
    }


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def schedule_trip(trip_data: TripCreate, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    shipment, vehicle, driver = get_dependencies_or_404(db, trip_data.shipment_id, trip_data.vehicle_id, trip_data.driver_id)
    if driver.status == DriverStatus.Inactive:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An inactive driver cannot be scheduled for a trip.")
    if shipment.status in {ShipmentStatus.Delivered, ShipmentStatus.Cancelled}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A delivered or cancelled shipment cannot be scheduled for a trip.")
    if vehicle.status != VehicleStatus.Available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected vehicle is not available for assignment.")
    if has_other_committed_trip(
        db,
        vehicle_id=trip_data.vehicle_id,
        driver_id=trip_data.driver_id,
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected vehicle or driver already has a scheduled or active trip.")
    if shipment.status == ShipmentStatus.Created:
        shipment.status = ShipmentStatus.Assigned
    driver.status = DriverStatus.Offline
    vehicle.status = VehicleStatus.Assigned
    vehicle.assigned_driver = trip_data.driver_id
    return create_trip(db, trip_data)


@router.get("/", response_model=list[TripResponse])
def list_trips(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value not in {"Admin", "FleetManager", "Dispatcher", "Driver"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view trips.")
    return get_trips_for_user(db, current_user)


@router.get("/{trip_id}", response_model=TripResponse)
def get_single_trip(trip_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    require_trip_access(db, trip, current_user)
    return trip


@router.post("/{trip_id}/route", response_model=TripRouteResponse)
def calculate_trip_route(trip_id: UUID, route_request: RouteCalculationRequest | None = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    require_admin_or_fleet_manager(current_user)
    if trip.status != TripStatus.Scheduled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Routes can be calculated only for scheduled trips.")
    # A second explicit Calculate Route action is the project's route-change
    # event. Keep the existing Scheduled-only rule: active GPS updates change
    # ETA, not route geometry, so they must never create route notifications.
    had_saved_route = trip.route_geometry is not None
    route_type = route_request.route_type if route_request and route_request.route_type else trip.route_type
    route_data = build_route(trip.source, trip.destination, route_type)
    if "error" in route_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=route_data["error"])
    trip = save_route(db, trip, route_data, route_type)
    if had_saved_route:
        driver = db.query(Driver).filter(Driver.driver_id == trip.driver_id).first()
        if driver and driver.user_id:
            create_notification(
                db,
                user_id=driver.user_id,
                title="Route Updated",
                message=f"The route for trip {trip.trip_id} has been recalculated. ETA has been updated.",
                notification_type="route_change",
                # One explicit recalculation notification per trip prevents
                # repeated clicks from flooding the assigned driver's inbox.
                alert_type=f"route_change:{trip.trip_id}",
            )
    return route_response(db, trip, route_data["fallback"])


@router.get("/{trip_id}/route", response_model=TripRouteResponse)
def get_trip_route(trip_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    require_route_access(db, trip, current_user)
    if trip.route_geometry is None or trip.planned_distance is None or trip.estimated_duration is None or trip.eta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No calculated route exists for this trip.")
    return route_response(db, trip)


@router.put("/{trip_id}", response_model=TripResponse)
def update_scheduled_trip(trip_id: UUID, trip_data: TripUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    trip = get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.status != TripStatus.Scheduled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only scheduled trips can be updated.")
    values = trip_data.model_dump(exclude_unset=True)
    shipment_id = values.get("shipment_id", trip.shipment_id)
    vehicle_id = values.get("vehicle_id", trip.vehicle_id)
    driver_id = values.get("driver_id", trip.driver_id)
    shipment, vehicle, driver = get_dependencies_or_404(db, shipment_id, vehicle_id, driver_id)
    if driver.status == DriverStatus.Inactive:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An inactive driver cannot be scheduled for a trip.")
    if shipment.status in {ShipmentStatus.Delivered, ShipmentStatus.Cancelled}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A delivered or cancelled shipment cannot be scheduled for a trip.")
    if vehicle_id != trip.vehicle_id and vehicle.status != VehicleStatus.Available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected vehicle is not available for assignment.")
    if vehicle_id == trip.vehicle_id and vehicle.status not in {
        VehicleStatus.Available,
        VehicleStatus.Assigned,
    }:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected vehicle is not available for assignment.")
    if has_other_committed_trip(
        db,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        excluded_trip_id=trip.trip_id,
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected vehicle or driver already has a scheduled or active trip.")
    if shipment.status == ShipmentStatus.Created:
        shipment.status = ShipmentStatus.Assigned
    if driver_id != trip.driver_id:
        previous_driver = db.query(Driver).filter(Driver.driver_id == trip.driver_id).first()
        if previous_driver and previous_driver.status != DriverStatus.Inactive:
            other_trip = db.query(Trip).filter(
                Trip.driver_id == previous_driver.driver_id,
                Trip.status.in_([TripStatus.Scheduled, TripStatus.Active]),
                Trip.trip_id != trip.trip_id,
            ).first()
            if other_trip is None:
                previous_driver.status = DriverStatus.Available
    driver.status = DriverStatus.Offline
    if vehicle_id != trip.vehicle_id:
        previous_vehicle = db.query(Vehicle).filter(
            Vehicle.vehicle_id == trip.vehicle_id
        ).first()
        if previous_vehicle:
            previous_vehicle.status = VehicleStatus.Available
            previous_vehicle.assigned_driver = None
    vehicle.status = VehicleStatus.Assigned
    vehicle.assigned_driver = driver_id
    return update_trip(db, trip, trip_data)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager),
):
    trip = get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.status == TripStatus.Active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An active trip cannot be deleted. End the trip first.")
    if trip.status == TripStatus.Completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A completed trip cannot be deleted.")
    delete_scheduled_trip(db, trip)


@router.patch("/{trip_id}/start", response_model=TripResponse)
async def start_scheduled_trip(trip_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    require_start_end_permission(db, trip, current_user)
    if trip.status != TripStatus.Scheduled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only scheduled trips can be started.")
    shipment, vehicle, driver = get_dependencies_or_404(db, trip.shipment_id, trip.vehicle_id, trip.driver_id)
    if getattr(driver.status, "value", driver.status) == "Inactive":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An inactive driver cannot start a trip.")
    if has_other_committed_trip(db, vehicle_id=trip.vehicle_id, driver_id=trip.driver_id, excluded_trip_id=trip.trip_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected vehicle or driver already has a scheduled or active trip.")
    if shipment.status not in {ShipmentStatus.Assigned, ShipmentStatus.InTransit}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The shipment must be assigned before its trip can start.")
    if not trip.route_geometry or trip.planned_distance is None or trip.estimated_duration is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Calculate and save the route before starting this trip.")
    started_trip = start_trip(db, trip, vehicle, shipment)
    await gps_simulator.start(started_trip.trip_id, started_trip.vehicle_id)
    return started_trip


@router.patch("/{trip_id}/end", response_model=TripResponse)
async def end_active_trip(trip_id: UUID, end_data: TripEnd, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    trip = get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    require_start_end_permission(db, trip, current_user)
    if trip.status != TripStatus.Active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A trip must be active before it can be ended.")
    shipment, vehicle, _ = get_dependencies_or_404(db, trip.shipment_id, trip.vehicle_id, trip.driver_id)
    completed_trip = end_trip(db, trip, vehicle, shipment, end_data)
    await gps_simulator.stop(completed_trip.vehicle_id)
    return completed_trip
