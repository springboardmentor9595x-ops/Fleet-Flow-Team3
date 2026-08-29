from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FuelRecordCreate(BaseModel):
    vehicle_id: UUID
    fuel_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    fuel_cost: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    mileage: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    refill_date: datetime


class FuelRecordUpdate(BaseModel):
    vehicle_id: UUID | None = None
    fuel_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=3)
    fuel_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    mileage: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    refill_date: datetime | None = None


class FuelRecordResponse(BaseModel):
    fuel_id: UUID
    fuel_reference: str | None = None
    vehicle_id: UUID | None = None
    fuel_amount: Decimal | None = None
    fuel_cost: Decimal | None = None
    mileage: Decimal | None = None
    refill_date: datetime | None = None

    class Config:
        from_attributes = True
