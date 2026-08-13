from pydantic import BaseModel
from uuid import UUID


class DriverCreate(BaseModel):
    user_id: UUID | None = None


class DriverUpdate(BaseModel):
    user_id: UUID | None = None


class DriverOut(BaseModel):
    driver_id: UUID
    user_id: UUID | None = None

    # User information
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None

    # Vehicle information
    vehicle_id: UUID | None = None
    registration_number: str | None = None
    vehicle_status: str | None = None

    class Config:
        from_attributes = True