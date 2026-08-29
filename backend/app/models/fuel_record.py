import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class FuelRecord(Base):
    __tablename__ = "fuel_records"

    fuel_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    vehicle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.vehicle_id"),
        nullable=True,
    )

    # Human-readable, backend-generated display identifier. The UUID primary
    # key remains the stable API/database identifier for backwards compatibility.
    fuel_reference = Column(String(20), unique=True, index=True, nullable=True)

    # Nullable at the database level so the additive migration preserves any
    # pre-existing stub rows. The fuel API requires these values for new data.
    fuel_amount = Column(Numeric(12, 3), nullable=True)
    fuel_cost = Column(Numeric(12, 2), nullable=True)
    mileage = Column(Numeric(12, 2), nullable=True)
    refill_date = Column(DateTime(timezone=True), nullable=True)
