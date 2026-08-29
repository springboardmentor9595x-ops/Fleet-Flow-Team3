from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


DriverStatusValue = Literal["Available", "On Trip", "Offline", "Inactive"]


class AssignedVehicleResponse(BaseModel):
    vehicle_id: UUID
    registration_number: str
    status: str


class CurrentTripResponse(BaseModel):
    trip_id: UUID
    source: str
    destination: str
    status: str
    started_at: datetime | None = None


class DriverResponse(BaseModel):
    driver_id: UUID
    full_name: str | None
    user_id: UUID | None
    email: str | None = None
    phone: str | None = None
    license_number: str | None = None
    experience_years: int = 0
    address: str | None = None
    status: DriverStatusValue = "Available"
    assigned_vehicle_id: UUID | None = None
    assigned_vehicle: AssignedVehicleResponse | None = None
    current_trip: CurrentTripResponse | None = None

    class Config:
        from_attributes = True


class DriverCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    user_id: UUID
    license_number: str | None = Field(default=None, min_length=1, max_length=50)
    experience_years: int = Field(default=0, ge=0, le=80)
    address: str | None = Field(default=None, max_length=255)
    status: DriverStatusValue = "Available"


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    user_id: UUID | None = None
    license_number: str | None = Field(default=None, min_length=1, max_length=50)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    address: str | None = Field(default=None, max_length=255)
    status: DriverStatusValue | None = None
