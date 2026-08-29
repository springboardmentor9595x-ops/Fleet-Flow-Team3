import os

from celery import Celery
from celery.schedules import crontab


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "fleetflow",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.maintenance"],
)

celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "check-maintenance-alerts-daily": {
            "task": "app.tasks.maintenance.check_maintenance_alerts",
            "schedule": crontab(hour=8, minute=0),
        }
    },
)
