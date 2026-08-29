import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class MaintenanceStatus(str, enum.Enum):
    Scheduled = "Scheduled"
    InProgress = "InProgress"
    Completed = "Completed"
    Cancelled = "Cancelled"
    Resolved = "Resolved"


class Maintenance(Base):
    __tablename__ = "maintenance"

    maintenance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    maintenance_type = Column(String(100), nullable=False)
    service_date = Column(DateTime(timezone=True), nullable=False, index=True)
    next_service_date = Column(DateTime(timezone=True), nullable=True, index=True)
    cost = Column(Numeric(12, 2), nullable=True)
    remarks = Column(Text, nullable=True)
    status = Column(
        Enum(
            MaintenanceStatus,
            name="maintenance_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=MaintenanceStatus.Scheduled,
        server_default=MaintenanceStatus.Scheduled.value,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_notes = Column(Text, nullable=True)
    upcoming_alert_sent = Column(Boolean, nullable=False, default=False, server_default="false")
    overdue_alert_sent = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
