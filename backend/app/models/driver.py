import enum
import uuid

from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class DriverStatus(str, enum.Enum):
    Available = "Available"
    OnTrip = "On Trip"
    Offline = "Offline"
    Inactive = "Inactive"


class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        unique=True,
        nullable=True,
    )

    full_name = Column(
        String(100),
        nullable=True,
    )

    license_number = Column(
        String(50),
        unique=True,
        nullable=True,
    )

    experience_years = Column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    address = Column(
        String(255),
        nullable=True,
    )

    status = Column(
        Enum(
            DriverStatus,
            name="driver_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=DriverStatus.Available,
        server_default=DriverStatus.Available.value,
    )
