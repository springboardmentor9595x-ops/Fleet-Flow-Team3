from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.shipment import ShipmentStatus


# ============================================================
# CREATE SHIPMENT
# ============================================================

class ShipmentCreate(BaseModel):

    tracking_number: str
    source: str
    destination: str
    customer_name: str
    shipment_weight: float

    vehicle_id: UUID | None = None
    driver_id: UUID | None = None

    status: ShipmentStatus = ShipmentStatus.Created


# ============================================================
# UPDATE SHIPMENT
# ============================================================

class ShipmentUpdate(BaseModel):

    tracking_number: str | None = None
    source: str | None = None
    destination: str | None = None
    customer_name: str | None = None
    shipment_weight: float | None = None

    vehicle_id: UUID | None = None
    driver_id: UUID | None = None

    status: ShipmentStatus | None = None


# ============================================================
# SHIPMENT OUTPUT
# ============================================================

class ShipmentOut(BaseModel):

    shipment_id: UUID

    tracking_number: str
    source: str
    destination: str
    customer_name: str
    shipment_weight: float

    vehicle_id: UUID | None
    driver_id: UUID | None

    status: ShipmentStatus

    model_config = ConfigDict(
        from_attributes=True
    )