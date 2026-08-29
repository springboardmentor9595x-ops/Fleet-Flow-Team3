import uuid
import enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Enum,
    DateTime,
    ForeignKey,
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database import Base


class VehicleStatus(str, enum.Enum):
    Available = "Available"
    Assigned = "Assigned"
    Maintenance = "Maintenance"
    InTransit = "In Transit"


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    registration_number = Column(
        String(20),
        unique=True,
        nullable=False
    )

    vehicle_type = Column(
        String(50),
        nullable=False
    )

    brand = Column(
        String(50),
        nullable=False
    )

    model = Column(
        String(50),
        nullable=False
    )

    manufacture_year = Column(
        Integer,
        nullable=False
    )

    fuel_type = Column(
        String(30),
        nullable=False
    )

    capacity = Column(
        Integer,
        nullable=False
    )

    assigned_driver = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.driver_id"),
        nullable=True
    )

    status = Column(
    Enum(
        VehicleStatus,
        name="vehicle_status",
        values_callable=lambda enum_class: [e.value for e in enum_class]
    ),
    default=VehicleStatus.Available,
    nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )