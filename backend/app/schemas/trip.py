from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.trip import TripStatus


RouteType = Literal["Shortest", "Fastest", "Eco", "Balanced"]


class TripCreate(BaseModel):
    shipment_id: UUID
    vehicle_id: UUID
    driver_id: UUID
    source: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    route_type: RouteType = "Fastest"
    planned_distance: float | None = Field(default=None, ge=0)
    estimated_duration: float | None = Field(default=None, ge=0)
    eta: datetime | None = None


class TripUpdate(BaseModel):
    shipment_id: UUID | None = None
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    source: str | None = Field(default=None, min_length=1, max_length=255)
    destination: str | None = Field(default=None, min_length=1, max_length=255)
    route_type: RouteType | None = None
    planned_distance: float | None = Field(default=None, ge=0)
    estimated_duration: float | None = Field(default=None, ge=0)
    eta: datetime | None = None


class TripEnd(BaseModel):
    actual_distance_meters: float | None = Field(default=None, ge=0)


class RouteCalculationRequest(BaseModel):
    route_type: RouteType | None = None


class TripRouteResponse(BaseModel):
    trip_id: UUID
    route_type: RouteType
    planned_distance: float
    estimated_duration: float
    eta: datetime
    remaining_distance: float | None
    remaining_duration: float | None
    geometry: list[list[float]]
    fallback: bool


class TripResponse(BaseModel):
    trip_id: UUID
    shipment_id: UUID
    vehicle_id: UUID
    driver_id: UUID
    source: str
    destination: str
    route_type: str
    planned_distance: float | None
    estimated_duration: float | None
    eta: datetime | None
    status: TripStatus
    started_at: datetime | None
    ended_at: datetime | None
    actual_distance_meters: float | None
    created_at: datetime

    class Config:
        from_attributes = True
