"""Centralized creation and recipient selection for in-app notifications."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.driver import Driver
from app.models.user import RoleEnum, User
from app.models.vehicle import Vehicle


def operations_user_ids(db: Session, *, include_dispatcher: bool = True) -> list[UUID]:
    roles = [RoleEnum.Admin, RoleEnum.FleetManager]
    if include_dispatcher:
        roles.append(RoleEnum.Dispatcher)
    return [row.user_id for row in db.query(User.user_id).filter(User.role.in_(roles)).all()]


def maintenance_recipient_ids(db: Session, vehicle_id: UUID | None = None) -> list[UUID]:
    """Notify fleet managers plus the driver assigned to the affected vehicle."""
    recipients = [
        row.user_id
        for row in db.query(User.user_id).filter(
            User.role.in_([RoleEnum.Admin, RoleEnum.FleetManager])
        ).all()
    ]
    if vehicle_id is not None:
        assigned_driver = (
            db.query(Driver.user_id)
            .join(Vehicle, Vehicle.assigned_driver == Driver.driver_id)
            .filter(Vehicle.vehicle_id == vehicle_id, Driver.user_id.isnot(None))
            .first()
        )
        if assigned_driver is not None:
            recipients.append(assigned_driver.user_id)
    return list(dict.fromkeys(recipients))


def create_notification(
    db: Session,
    *,
    user_id: UUID | None,
    title: str,
    message: str,
    notification_type: str,
    maintenance_id: UUID | None = None,
    alert_type: str | None = None,
) -> Notification | None:
    """Create one notification, returning None when its event was already recorded."""
    if alert_type:
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.alert_type == alert_type,
        )
        if maintenance_id is not None:
            query = query.filter(Notification.maintenance_id == maintenance_id)
        if query.first() is not None:
            return None

    now = datetime.now(timezone.utc)
    notification = Notification(
        user_id=user_id,
        maintenance_id=maintenance_id,
        alert_type=alert_type,
        title=title,
        message=message,
        type=notification_type,
        is_read=False,
        created_at=now,
        sent_at=now,
        delivered=True,
    )
    db.add(notification)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    db.refresh(notification)
    return notification
