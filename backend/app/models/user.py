import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RoleEnum(str, enum.Enum):
    Admin = "Admin"
    FleetManager = "FleetManager"
    Driver = "Driver"
    Dispatcher = "Dispatcher"


class User(Base):
    __tablename__ = "users"

    # Primary Key
    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # User name
    full_name = Column(
        String(100),
        nullable=False
    )

    # Email
    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # Password
    password = Column(
        String(255),
        nullable=False
    )

    # Phone
    phone = Column(
        String(15),
        nullable=True
    )

    # Role
    role = Column(
        String(30),
        nullable=False,
        default=RoleEnum.Driver.value
    )

    # Created timestamp
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Updated timestamp
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship with Driver
    driver = relationship(
        "Driver",
        back_populates="user",
        uselist=False
    )