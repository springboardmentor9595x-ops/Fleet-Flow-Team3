"""Single calendar-period resolver used by every FleetFlow report."""
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from fastapi import HTTPException, status


@dataclass(frozen=True)
class ReportPeriod:
    period_type: str
    start_date: date
    end_date: date

    def as_dict(self) -> dict:
        return {"type": self.period_type, "start_date": self.start_date.isoformat(), "end_date": self.end_date.isoformat()}

    @property
    def start_datetime(self) -> datetime:
        return datetime.combine(self.start_date, time.min, tzinfo=timezone.utc)

    @property
    def end_datetime(self) -> datetime:
        return datetime.combine(self.end_date, time.max, tzinfo=timezone.utc)


def resolve_report_period(
    period: str = "current_week",
    month: int | None = None,
    year: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    today: date | None = None,
) -> ReportPeriod:
    """Resolve calendar ranges; previous_week is never interpreted as last 7 days."""
    today = today or date.today()
    if period == "previous_week":
        current_monday = today.fromordinal(today.toordinal() - today.weekday())
        end = current_monday.fromordinal(current_monday.toordinal() - 1)
        return ReportPeriod(period, end.fromordinal(end.toordinal() - 6), end)
    if period == "current_week":
        return ReportPeriod(period, today.fromordinal(today.toordinal() - today.weekday()), today)
    if period == "monthly":
        if month is None or year is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month and year are required for monthly reports.")
        try:
            last_day = monthrange(year, month)[1]
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must be 1 through 12 and year must be valid.")
        return ReportPeriod(period, date(year, month, 1), date(year, month, last_day))
    if period == "custom":
        if start_date is None or end_date is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date and end_date are required for custom reports.")
        if start_date > end_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be earlier than or equal to end_date.")
        return ReportPeriod(period, start_date, end_date)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="period must be previous_week, current_week, monthly, or custom.")
