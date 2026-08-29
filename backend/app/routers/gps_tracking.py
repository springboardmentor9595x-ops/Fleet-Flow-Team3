import asyncio
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.geofence import get_geofence_event, is_inside_zone
from app.core.deps import get_current_user
from app.core.redis_client import gps_pubsub
from app.core.security import verify_token
from app.crud.gps_tracking import (
    create_gps_location,
    get_latest_gps_locations,
)
from app.crud.trip import has_active_trip_for_vehicle, update_active_trip_eta
from app.crud.user import get_user_by_email
from app.models.driver import Driver
from app.models.trip import Trip, TripStatus
from app.models.user import RoleEnum
from app.models.vehicle import Vehicle
from app.schemas.gps_tracking import (
    GPSLocationCreate,
    GPSLocationResponse,
    GPSWebSocketUpdate,
    
)
from database import SessionLocal, get_db


HEARTBEAT_TIMEOUT_SECONDS = 30
STALE_CONNECTION_SECONDS = 90

router = APIRouter(
    prefix="/gps",
    tags=["GPS Tracking"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}
        self.last_seen: dict[WebSocket, datetime] = {}
        self.geofence_states: dict[tuple[str, str], bool] = {}

    async def connect(self, vehicle_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(str(vehicle_id), set()).add(websocket)
        self.last_seen[websocket] = datetime.now(timezone.utc)

    def mark_alive(self, websocket: WebSocket) -> None:
        self.last_seen[websocket] = datetime.now(timezone.utc)

    def disconnect(self, vehicle_id: UUID, websocket: WebSocket) -> None:
        vehicle_key = str(vehicle_id)
        connections = self.active_connections.get(vehicle_key)
        if connections:
            connections.discard(websocket)
            if not connections:
                self.active_connections.pop(vehicle_key, None)
        self.last_seen.pop(websocket, None)

    async def broadcast(self, vehicle_id: UUID, message: dict) -> None:
        disconnected: list[WebSocket] = []
        for websocket in list(self.active_connections.get(str(vehicle_id), set())):
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(vehicle_id, websocket)

    async def cleanup_stale_connections(self, vehicle_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        for websocket in list(self.active_connections.get(str(vehicle_id), set())):
            last_seen = self.last_seen.get(websocket, now)
            if now - last_seen <= timedelta(seconds=STALE_CONNECTION_SECONDS):
                continue
            self.disconnect(vehicle_id, websocket)
            try:
                await websocket.close(code=1001, reason="Stale connection")
            except Exception:
                pass

    async def cleanup_all_stale_connections(self) -> None:
        for vehicle_key in list(self.active_connections):
            await self.cleanup_stale_connections(UUID(vehicle_key))

    def geofence_message(
        self,
        vehicle_id: UUID,
        update: GPSWebSocketUpdate,
    ) -> dict | None:
        if update.destination_latitude is None or update.destination_longitude is None:
            return None

        zone_key = (
            str(vehicle_id),
            f"{update.destination_latitude}:{update.destination_longitude}:{update.geofence_radius_meters}",
        )
        inside = is_inside_zone(
            update.latitude,
            update.longitude,
            update.destination_latitude,
            update.destination_longitude,
            update.geofence_radius_meters,
        )
        event_type = get_geofence_event(self.geofence_states.get(zone_key), inside)
        self.geofence_states[zone_key] = inside

        if event_type is None:
            return None

        return {
            "type": event_type,
            "vehicle_id": str(vehicle_id),
            "destination_latitude": update.destination_latitude,
            "destination_longitude": update.destination_longitude,
            "radius_meters": update.geofence_radius_meters,
        }


manager = ConnectionManager()
_stale_cleanup_task: asyncio.Task | None = None


def driver_can_access_vehicle(db: Session, current_user, vehicle_id: UUID) -> bool:
    """Check ownership through either the assignment or an active/scheduled trip."""
    driver = db.query(Driver).filter(Driver.user_id == current_user.user_id).first()
    if driver is None:
        return False
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if vehicle and vehicle.assigned_driver == driver.driver_id:
        return True
    return db.query(Trip).filter(
        Trip.driver_id == driver.driver_id,
        Trip.vehicle_id == vehicle_id,
        Trip.status.in_([TripStatus.Scheduled, TripStatus.Active]),
    ).first() is not None


def require_tracking_view_access(db: Session, current_user, vehicle_id: UUID) -> None:
    if current_user.role in {RoleEnum.Admin, RoleEnum.FleetManager, RoleEnum.Dispatcher}:
        return
    if current_user.role == RoleEnum.Driver and driver_can_access_vehicle(db, current_user, vehicle_id):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Drivers can view tracking only for their assigned vehicle.",
    )


def require_location_publish_access(db: Session, current_user, vehicle_id: UUID) -> None:
    if current_user.role in {RoleEnum.Admin, RoleEnum.FleetManager}:
        return
    if current_user.role == RoleEnum.Driver and driver_can_access_vehicle(db, current_user, vehicle_id):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to publish GPS data for this vehicle.",
    )


async def websocket_current_user(websocket: WebSocket):
    """Authenticate a browser WebSocket token before accepting the socket."""
    token = websocket.query_params.get("token")
    payload = verify_token(token) if token else None
    email = payload.get("sub") if payload else None
    if not email:
        await websocket.close(code=1008, reason="Authentication required")
        return None
    db = SessionLocal()
    try:
        return get_user_by_email(db, email)
    finally:
        db.close()


async def broadcast_vehicle_message(vehicle_id: UUID, message: dict) -> None:
    """Broadcast locally first, then forward the event to other instances."""
    await manager.broadcast(vehicle_id, message)
    await gps_pubsub.publish(vehicle_id, message)


async def _broadcast_from_redis(vehicle_id: UUID, message: dict) -> None:
    await manager.broadcast(vehicle_id, message)


async def _stale_connection_loop() -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_TIMEOUT_SECONDS)
        await manager.cleanup_all_stale_connections()


async def start_gps_reliability_services() -> None:
    """Start optional Redis forwarding and independent stale-connection cleanup."""
    global _stale_cleanup_task
    await gps_pubsub.start(_broadcast_from_redis)
    if _stale_cleanup_task is None or _stale_cleanup_task.done():
        _stale_cleanup_task = asyncio.create_task(
            _stale_connection_loop(), name="fleetflow-gps-stale-cleanup"
        )


async def stop_gps_reliability_services() -> None:
    global _stale_cleanup_task
    if _stale_cleanup_task and not _stale_cleanup_task.done():
        _stale_cleanup_task.cancel()
        try:
            await _stale_cleanup_task
        except asyncio.CancelledError:
            pass
    _stale_cleanup_task = None
    await gps_pubsub.stop()


def calculate_heading(lat1, lon1, lat2, lon2):
    """Return the compass bearing from the previous point to the latest point."""
    d_lon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    x = math.sin(d_lon) * math.cos(lat2)
    y = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    )

    bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
    return round(bearing, 1)


def latest_heading(db: Session, vehicle_id: UUID) -> float | None:
    """Derive heading from newest two GPS records without changing the table."""
    locations = get_latest_gps_locations(db, vehicle_id, limit=2)
    if len(locations) < 2:
        return None

    latest, previous = locations
    return calculate_heading(
        previous.latitude,
        previous.longitude,
        latest.latitude,
        latest.longitude,
    )


def location_message(location, heading: float | None = None) -> dict:
    payload = GPSLocationResponse.model_validate(
        location
    ).model_dump(mode="json")
    payload["heading"] = heading
    return {"type": "location_update", "location": payload}


async def broadcast_gps_location(
    location,
    heading: float | None = None,
    destination: tuple[float, float] | None = None,
) -> None:
    """Send a persisted location to viewers and emit its geofence event."""
    db = SessionLocal()
    try:
        if heading is None:
            heading = latest_heading(db, location.vehicle_id)
        # Persisted GPS remains available for auditing, but scheduled trips do
        # not emit live movement or ETA updates until Start Trip succeeds.
        if not has_active_trip_for_vehicle(db, location.vehicle_id):
            return
        trip_metrics = update_active_trip_eta(db, location.vehicle_id, location)
    finally:
        db.close()

    message = location_message(location, heading)
    if trip_metrics:
        message["trip_metrics"] = trip_metrics
    await broadcast_vehicle_message(location.vehicle_id, message)

    if destination is None:
        return

    destination_latitude, destination_longitude = destination
    geofence_event = manager.geofence_message(
        location.vehicle_id,
        GPSWebSocketUpdate(
            latitude=location.latitude,
            longitude=location.longitude,
            speed=location.speed,
            destination_latitude=destination_latitude,
            destination_longitude=destination_longitude,
        ),
    )
    if geofence_event:
        await broadcast_vehicle_message(location.vehicle_id, geofence_event)


def persist_websocket_location(vehicle_id: UUID, update: GPSWebSocketUpdate):
    db = SessionLocal()
    try:
        return create_gps_location(
            db,
            GPSLocationCreate(
                vehicle_id=vehicle_id,
                latitude=update.latitude,
                longitude=update.longitude,
                speed=update.speed,
            ),
        )
    finally:
        db.close()


@router.post("/location", response_model=GPSLocationResponse)
async def receive_gps_location(
    gps_data: GPSLocationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_location_publish_access(db, current_user, gps_data.vehicle_id)
    location = create_gps_location(db, gps_data)
    await broadcast_gps_location(location)
    return location


@router.websocket("/ws/{vehicle_id}")
async def gps_websocket(websocket: WebSocket, vehicle_id: UUID):
    current_user = await websocket_current_user(websocket)
    if current_user is None:
        return

    db = SessionLocal()
    try:
        require_tracking_view_access(db, current_user, vehicle_id)
    except HTTPException:
        await websocket.close(code=1008, reason="Tracking access denied")
        return
    finally:
        db.close()

    await manager.connect(vehicle_id, websocket)

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=HEARTBEAT_TIMEOUT_SECONDS,
                )
            except TimeoutError:
                await manager.cleanup_stale_connections(vehicle_id)
                if websocket not in manager.active_connections.get(str(vehicle_id), set()):
                    return
                await websocket.send_json({"type": "ping"})
                continue

            manager.mark_alive(websocket)
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
                continue

            db = SessionLocal()
            try:
                require_location_publish_access(db, current_user, vehicle_id)
            except HTTPException as error:
                await websocket.send_json({"type": "error", "detail": error.detail})
                continue
            finally:
                db.close()

            try:
                update = GPSWebSocketUpdate.model_validate(data)
                location = persist_websocket_location(vehicle_id, update)
            except ValidationError as error:
                await websocket.send_json({"type": "error", "detail": error.errors()})
                continue
            except Exception:
                await websocket.send_json({"type": "error", "detail": "Unable to store GPS update."})
                continue

            await broadcast_gps_location(
                location,
                destination=(
                    update.destination_latitude,
                    update.destination_longitude,
                )
                if update.destination_latitude is not None
                and update.destination_longitude is not None
                else None,
            )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(vehicle_id, websocket)
@router.get("/latest/{vehicle_id}", response_model=GPSLocationResponse)
def get_latest_location(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_tracking_view_access(db, current_user, vehicle_id)
    locations = get_latest_gps_locations(db, vehicle_id, limit=2)
    if not locations:
        raise HTTPException(
            status_code=404,
            detail="No GPS location found for this vehicle.",
        )

    location = locations[0]
    heading = None
    if len(locations) > 1:
        previous = locations[1]
        heading = calculate_heading(
            previous.latitude,
            previous.longitude,
            location.latitude,
            location.longitude,
        )

    return GPSLocationResponse.model_validate(location).model_copy(
        update={"heading": heading}
    )
