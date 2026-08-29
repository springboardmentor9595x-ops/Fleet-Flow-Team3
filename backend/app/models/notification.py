import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "maintenance_id",
            "user_id",
            "alert_type",
            name="uq_notifications_maintenance_user_alert_type",
        ),
    )

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    maintenance_id = Column(UUID(as_uuid=True), ForeignKey("maintenance.maintenance_id"), nullable=True, index=True)
    # Legacy maintenance fields are retained for compatibility and event-level
    # deduplication. New notification consumers use title/message/type below.
    alert_type = Column(String(120), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc))
    delivered = Column(Boolean, nullable=False, default=False, server_default="false")
    title = Column(String(160), nullable=False, default="FleetFlow notification", server_default="FleetFlow notification")
    message = Column(Text, nullable=False, default="", server_default="")
    type = Column(String(50), nullable=False, default="system", server_default="system")
    is_read = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), server_default="CURRENT_TIMESTAMP")
