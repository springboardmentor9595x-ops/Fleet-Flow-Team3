"""Server-side GPS simulation for Active trips with stored OSRM geometry."""
import asyncio
from math import atan2, cos, radians, sin
from uuid import UUID

from app.crud.gps_tracking import create_gps_location
from app.models.trip import Trip, TripStatus
from app.routers.gps_tracking import broadcast_gps_location
from app.schemas.gps_tracking import GPSLocationCreate
from database import SessionLocal


UPDATE_INTERVAL_SECONDS = 2.5
SIMULATION_STEPS = 80


class GPSSimulator:
    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}

    @staticmethod
    def _sample_route(geometry: list) -> list[list[float]]:
        if len(geometry) <= SIMULATION_STEPS:
            return geometry
        stride = max(1, len(geometry) // SIMULATION_STEPS)
        sampled = geometry[::stride]
        if sampled[-1] != geometry[-1]:
            sampled.append(geometry[-1])
        return sampled

    @staticmethod
    def _heading(previous: list[float], current: list[float]) -> float:
        lon1, lat1 = map(radians, previous)
        lon2, lat2 = map(radians, current)
        delta_lon = lon2 - lon1
        x = sin(delta_lon) * cos(lat2)
        y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(delta_lon)
        return (atan2(x, y) * 180 / 3.141592653589793 + 360) % 360

    async def start(self, trip_id: UUID, vehicle_id: UUID) -> None:
        vehicle_key = str(vehicle_id)
        existing = self._tasks.get(vehicle_key)
        if existing and not existing.done():
            return
        self._tasks[vehicle_key] = asyncio.create_task(
            self._run(trip_id, vehicle_id),
            name=f"gps-simulator-{vehicle_key}",
        )

    async def stop(self, vehicle_id: UUID) -> None:
        task = self._tasks.pop(str(vehicle_id), None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _run(self, trip_id: UUID, vehicle_id: UUID) -> None:
        vehicle_key = str(vehicle_id)
        try:
            db = SessionLocal()
            try:
                trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
                geometry = trip.route_geometry if trip else None
            finally:
                db.close()

            if not geometry or len(geometry) < 2:
                return

            points = self._sample_route(geometry)
            destination = (points[-1][1], points[-1][0])
            for index, point in enumerate(points):
                db = SessionLocal()
                try:
                    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
                    if not trip or trip.status != TripStatus.Active:
                        return

                    previous = points[index - 1] if index else point
                    heading = self._heading(previous, point) if index else 0
                    speed = 38 + (index % 5) * 6
                    location = create_gps_location(
                        db,
                        GPSLocationCreate(
                            vehicle_id=vehicle_id,
                            latitude=point[1],
                            longitude=point[0],
                            speed=speed,
                        ),
                    )
                finally:
                    db.close()

                await broadcast_gps_location(
                    location,
                    heading=heading,
                    destination=destination,
                )
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise
        finally:
            task = self._tasks.get(vehicle_key)
            if task is asyncio.current_task():
                self._tasks.pop(vehicle_key, None)


gps_simulator = GPSSimulator()
