import uuid
import enum

from sqlalchemy import Column, String, Float, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ShipmentStatus(str, enum.Enum):
    Created = "Created"
    Assigned = "Assigned"
    In_Transit = "In Transit"
    Delayed = "Delayed"
    Delivered = "Delivered"
    Cancelled = "Cancelled"


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    tracking_number = Column(
        String(100),
        unique=True,
        nullable=False
    )

    source = Column(
        String(255),
        nullable=False
    )

    destination = Column(
        String(255),
        nullable=False
    )

    customer_name = Column(
        String(150),
        nullable=False
    )

    shipment_weight = Column(
        Float,
        nullable=False
    )

    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id"),
        nullable=True
    )

    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.driver_id"),
        nullable=True
    )

    status = Column(
        Enum(
            ShipmentStatus,
            name="shipmentstatus"
        ),
        nullable=False,
        default=ShipmentStatus.Created
    )