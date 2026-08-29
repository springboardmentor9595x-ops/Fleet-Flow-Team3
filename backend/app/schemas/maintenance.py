from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.maintenance import MaintenanceStatus


MaintenanceType = Literal[
    "Oil Change",
    "Tire Replacement",
    "Engine Service",
    "Brake Service",
    "General Inspection",
]


class MaintenanceCreate(BaseModel):
    vehicle_id: UUID
    maintenance_type: MaintenanceType
    service_date: datetime
    next_service_date: datetime | None = None
    cost: Decimal | None = Field(default=None, ge=0)
    remarks: str | None = None


class MaintenanceUpdate(BaseModel):
    maintenance_type: MaintenanceType | None = None
    service_date: datetime | None = None
    next_service_date: datetime | None = None
    cost: Decimal | None = Field(default=None, ge=0)
    remarks: str | None = None
    status: MaintenanceStatus | None = None
    completion_notes: str | None = None


class MaintenanceResponse(BaseModel):
    maintenance_id: UUID
    vehicle_id: UUID
    maintenance_type: str
    service_date: datetime
    next_service_date: datetime | None
    cost: Decimal | None
    remarks: str | None
    status: MaintenanceStatus
    started_at: datetime | None
    completed_at: datetime | None
    completion_notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaintenanceAlertsResponse(BaseModel):
    upcoming: list[MaintenanceResponse]
    overdue: list[MaintenanceResponse]
