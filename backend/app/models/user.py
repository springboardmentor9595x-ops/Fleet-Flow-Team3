import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database import Base


class RoleEnum(str, enum.Enum):
    Admin = "Admin"
    FleetManager = "FleetManager"
    Driver = "Driver"
    Dispatcher = "Dispatcher"


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    full_name = Column(
        String(100),
        nullable=False,
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password = Column(
        String(255),
        nullable=False,
    )

    phone = Column(
        String(15),
        nullable=True,
    )

    role = Column(
        Enum(
            RoleEnum,
            name="user_role",
            values_callable=lambda enum_class: [
                role.value for role in enum_class
            ],
        ),
        nullable=False,
        default=RoleEnum.Driver,
    )

    # New accounts must confirm ownership of their email address before login.
    email_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Never store the actual six-digit code. Store only its SHA-256 hash.
    verification_code_hash = Column(String(64), nullable=True)
    verification_code_expires_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
