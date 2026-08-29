import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class GPSTracking(Base):
    __tablename__ = "gps_tracking"

    gps_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id"),
        nullable=False,
    )

    latitude = Column(
        Float,
        nullable=False,
    )

    longitude = Column(
        Float,
        nullable=False,
    )

    speed = Column(
        Float,
        nullable=True,
        default=0,
    )

    recorded_time = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )