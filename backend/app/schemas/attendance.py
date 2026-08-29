from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


AttendanceActivityValue = Literal[
    "Trip Started",
    "Trip Completed",
    "Attendance / Check-in",
    "Attendance / Check-out",
]


class AttendanceCreate(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class AttendanceResponse(BaseModel):
    attendance_id: UUID
    driver_id: UUID
    activity_type: AttendanceActivityValue
    occurred_at: datetime
    trip_id: UUID | None = None
    notes: str | None = None

    class Config:
        from_attributes = True
