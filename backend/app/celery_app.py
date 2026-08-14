import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "fleetflow_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.maintenance_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Schedule for maintenance check (e.g., run every 1 minute for demo purposes, normally daily)
celery_app.conf.beat_schedule = {
    "check-upcoming-maintenance": {
        "task": "app.tasks.maintenance_tasks.check_upcoming_maintenance",
        "schedule": 60.0,
    }
}
