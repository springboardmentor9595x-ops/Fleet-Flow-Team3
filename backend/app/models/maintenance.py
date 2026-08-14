import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Float, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class VehicleMaintenance(Base):
    __tablename__ = "vehicle_maintenance"

    maintenance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id"),
        nullable=True
    )
    maintenance_type = Column(String(100), nullable=True, default="General Inspection")
    service_date = Column(DateTime, default=datetime.utcnow)
    next_service_date = Column(DateTime, nullable=True)
    cost = Column(Float, default=0.0)
    remarks = Column(String(500), nullable=True)
    status = Column(String(50), default="Scheduled")
    performed_by = Column(String(100), nullable=True)
    alert_sent = Column(Boolean, default=False)