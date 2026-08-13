import uuid

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        unique=True,
        nullable=True
    )

    # Relationship with User
    user = relationship(
        "User",
        back_populates="driver"
    )

    # Relationship with Vehicles
    vehicles = relationship(
        "Vehicle",
        back_populates="driver"
    )