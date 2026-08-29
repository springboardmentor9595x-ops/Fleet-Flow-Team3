import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class ShipmentStatus(str, enum.Enum):
    Created = "Created"
    Assigned = "Assigned"
    InTransit = "In Transit"
    Delayed = "Delayed"
    Delivered = "Delivered"
    Cancelled = "Cancelled"


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tracking_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    source = Column(
        String(255),
        nullable=False,
    )

    destination = Column(
        String(255),
        nullable=False,
    )

    customer_name = Column(
        String(255),
        nullable=False,
    )

    shipment_weight = Column(
        Float,
        nullable=False,
    )

    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id"),
        nullable=True,
    )

    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.driver_id"),
        nullable=True,
    )

    status = Column(
        Enum(
            ShipmentStatus,
            name="shipment_status",
            values_callable=lambda enum_class: [
                status.value for status in enum_class
            ],
        ),
        nullable=False,
        default=ShipmentStatus.Created,
        server_default=ShipmentStatus.Created.value,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    expected_delivery_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )