from typing import Any
from pydantic import BaseModel


class ReportPeriodResponse(BaseModel):
    type: str
    start_date: str
    end_date: str


class ReportResponse(BaseModel):
    report_type: str
    period: ReportPeriodResponse
    summary: dict[str, Any]
    data: list[dict[str, Any]]
    limitations: list[str] = []
