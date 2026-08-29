import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.models.maintenance import Maintenance, MaintenanceStatus
from app.services.notification import create_notification, maintenance_recipient_ids
from celery_app import celery_app
from database import SessionLocal


logger = logging.getLogger(__name__)
BUSINESS_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _record_console_notification(db, maintenance: Maintenance, alert_type: str) -> bool:
    labels = {
        "due_in_5_days": ("Maintenance due in 5 days", "is due for service in 5 days."),
        "due_tomorrow": ("Maintenance due tomorrow", "is due for service tomorrow."),
        "due_today": ("Maintenance due today", "is due for service today."),
    }
    title, suffix = labels.get(alert_type, ("Maintenance overdue", "is overdue for service."))
    message = f"Vehicle {maintenance.vehicle_id} {suffix}"
    recipient_ids = maintenance_recipient_ids(db, maintenance.vehicle_id) or [None]
    created = False
    for user_id in recipient_ids:
        notification = create_notification(
            db,
            user_id=user_id,
            maintenance_id=maintenance.maintenance_id,
            alert_type=alert_type,
            title=title,
            message=message,
            notification_type="maintenance",
        )
        created = created or notification is not None
    if created:
        logger.warning("Maintenance %s alert for vehicle %s due on %s", alert_type, maintenance.vehicle_id, maintenance.service_date)
    return created


def process_maintenance_alerts(db, now: datetime | None = None) -> dict[str, int]:
    """Persist daily maintenance reminders without suppressing daily overdue alerts.

    A scheduled or in-progress record is due on ``service_date``. Five-day,
    one-day, and due-today reminder types are unique per record. Overdue types
    include the calendar date, so one alert is recorded on each overdue day
    until the record is completed, cancelled, or resolved.
    """
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(BUSINESS_TIMEZONE).date()
    active_statuses = [MaintenanceStatus.Scheduled, MaintenanceStatus.InProgress]
    records = (
        db.query(Maintenance)
        .filter(Maintenance.status.in_(active_statuses))
        .all()
    )
    detected = {"five_day": 0, "one_day": 0, "due_today": 0, "overdue": 0}
    created = {"five_day": 0, "one_day": 0, "due_today": 0, "overdue": 0}
    for maintenance in records:
        if maintenance.service_date is None:
            continue
        due_date = maintenance.service_date.astimezone(BUSINESS_TIMEZONE).date() if maintenance.service_date.tzinfo else maintenance.service_date.date()
        days_until_due = (due_date - today).days
        if days_until_due == 5:
            alert_type = "due_in_5_days"
            counter = "five_day"
        elif days_until_due == 1:
            alert_type = "due_tomorrow"
            counter = "one_day"
        elif days_until_due == 0:
            alert_type = "due_today"
            counter = "due_today"
        elif days_until_due < 0:
            alert_type = f"overdue_{today.isoformat()}"
            counter = "overdue"
        else:
            continue
        detected[counter] += 1
        if _record_console_notification(db, maintenance, alert_type):
            created[counter] += 1
    return {
        **detected,
        **{f"{name}_created": count for name, count in created.items()},
    }


@celery_app.task(name="app.tasks.maintenance.check_maintenance_alerts")
def check_maintenance_alerts() -> dict[str, int]:
    """Run the daily console/log maintenance reminder job."""
    db = SessionLocal()
    try:
        return process_maintenance_alerts(db)
    finally:
        db.close()
