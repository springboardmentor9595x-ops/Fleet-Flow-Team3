import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class TripStatus(str, enum.Enum):
    Scheduled = "Scheduled"
    Active = "Active"
    Completed = "Completed"
    Cancelled = "Cancelled"


class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.shipment_id"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.vehicle_id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.driver_id"), nullable=False)
    source = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    route_type = Column(String(30), nullable=False, default="Fastest")
    planned_distance = Column(Float, nullable=True)
    estimated_duration = Column(Float, nullable=True)
    eta = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(
            TripStatus,
            name="trip_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=TripStatus.Scheduled,
        server_default=TripStatus.Scheduled.value,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Retained for GPS and route-optimization integration in later milestones.
    actual_distance_meters = Column(Float, nullable=True)
    route_geometry = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
