from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import Notification
from app.core.deps import get_current_user


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


# --------------------------------
# Schemas
# --------------------------------

class NotificationCreate(BaseModel):
    user_id: UUID
    message: str


class NotificationOut(BaseModel):
    notification_id: UUID
    user_id: UUID
    message: str

    class Config:
        from_attributes = True


# --------------------------------
# GET ALL NOTIFICATIONS
# --------------------------------

@router.get(
    "/",
    response_model=list[NotificationOut],
)
def get_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Notification).all()


# --------------------------------
# CREATE NOTIFICATION
# --------------------------------

@router.post(
    "/",
    response_model=NotificationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = Notification(
        user_id=notification_data.user_id,
        message=notification_data.message,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


# --------------------------------
# GET SINGLE NOTIFICATION
# --------------------------------

@router.get(
    "/{notification_id}",
    response_model=NotificationOut,
)
def get_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return notification


# --------------------------------
# DELETE NOTIFICATION
# --------------------------------

@router.delete(
    "/{notification_id}",
)
def delete_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    db.delete(notification)
    db.commit()

    return {
        "message": "Notification deleted successfully"
    }