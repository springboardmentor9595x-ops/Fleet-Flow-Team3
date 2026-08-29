from uuid import UUID
from pydantic import BaseModel, Field

from app.models.vehicle import VehicleStatus


class VehicleCreate(BaseModel):
    registration_number: str
    vehicle_type: str
    brand: str
    model: str
    manufacture_year: int = Field(ge=1900, le=2100)
    fuel_type: str
    capacity: int = Field(gt=0)


class VehicleUpdate(VehicleCreate):
    status: VehicleStatus


class VehicleResponse(BaseModel):
    vehicle_id: UUID
    registration_number: str
    vehicle_type: str
    brand: str
    model: str
    manufacture_year: int
    fuel_type: str
    capacity: int
    assigned_driver: UUID | None = None
    status: VehicleStatus

    class Config:
        from_attributes = True
