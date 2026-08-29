from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.shipment import ShipmentStatus


class ShipmentCreate(BaseModel):
    tracking_number: str = Field(min_length=1, max_length=50)
    source: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    customer_name: str = Field(min_length=1, max_length=255)
    shipment_weight: float = Field(gt=0)

    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    expected_delivery_at: datetime | None = None


class ShipmentUpdate(BaseModel):
    source: str | None = Field(default=None, max_length=255)
    destination: str | None = Field(default=None, max_length=255)
    customer_name: str | None = Field(default=None, max_length=255)
    shipment_weight: float | None = Field(default=None, gt=0)

    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    expected_delivery_at: datetime | None = None


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus


class ShipmentResponse(BaseModel):
    shipment_id: UUID
    tracking_number: str
    source: str
    destination: str
    customer_name: str
    shipment_weight: float

    vehicle_id: UUID | None
    driver_id: UUID | None

    status: ShipmentStatus
    expected_delivery_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True