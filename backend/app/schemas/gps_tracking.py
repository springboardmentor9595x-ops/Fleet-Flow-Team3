from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GPSLocationCreate(BaseModel):
    vehicle_id: UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed: float = Field(default=0, ge=0)


class GPSLocationResponse(BaseModel):
    gps_id: UUID
    vehicle_id: UUID
    latitude: float
    longitude: float
    speed: float | None
    recorded_time: datetime
    # Calculated from the latest two records; it is intentionally not stored.
    heading: float | None = None

    class Config:
        from_attributes = True


class GPSWebSocketUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed: float = Field(default=0, ge=0)
    destination_latitude: float | None = Field(default=None, ge=-90, le=90)
    destination_longitude: float | None = Field(default=None, ge=-180, le=180)
    geofence_radius_meters: float = Field(default=500, gt=0)
