from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

from app.models.shipment import ShipmentStatus


class ShipmentCreate(BaseModel):
    tracking_number: str
    source: str
    destination: str
    customer_name: str
    shipment_weight: float
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None


class ShipmentUpdate(BaseModel):
    tracking_number: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    customer_name: Optional[str] = None
    shipment_weight: Optional[float] = None
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    status: Optional[ShipmentStatus] = None


class ShipmentOut(BaseModel):
    shipment_id: UUID
    tracking_number: str
    source: str
    destination: str
    customer_name: str
    shipment_weight: float
    vehicle_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    status: ShipmentStatus

    model_config = ConfigDict(from_attributes=True)