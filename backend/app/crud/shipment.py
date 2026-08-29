from uuid import UUID

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.services.notification import create_notification, operations_user_ids
from datetime import datetime, timezone, timedelta


ALLOWED_STATUS_TRANSITIONS = {
    ShipmentStatus.Created: {
        ShipmentStatus.Assigned,
        ShipmentStatus.Cancelled,
    },
    ShipmentStatus.Assigned: {
        ShipmentStatus.InTransit,
        ShipmentStatus.Cancelled,
    },
    ShipmentStatus.InTransit: {
        ShipmentStatus.Delayed,
        ShipmentStatus.Delivered,
    },
    ShipmentStatus.Delayed: {
        ShipmentStatus.InTransit,
    },
    ShipmentStatus.Delivered: set(),
    ShipmentStatus.Cancelled: set(),
}


def create_shipment(
    db: Session,
    shipment_data: ShipmentCreate,
):
    shipment = Shipment(
        tracking_number=shipment_data.tracking_number,
        source=shipment_data.source,
        destination=shipment_data.destination,
        customer_name=shipment_data.customer_name,
        shipment_weight=shipment_data.shipment_weight,
        vehicle_id=shipment_data.vehicle_id,
        driver_id=shipment_data.driver_id,
        status=ShipmentStatus.Created,
        expected_delivery_at=shipment_data.expected_delivery_at,
    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    return shipment


def get_shipment(
    db: Session,
    shipment_id: UUID,
):
    return (
        db.query(Shipment)
        .filter(Shipment.shipment_id == shipment_id)
        .first()
    )


def get_shipment_by_tracking_number(
    db: Session,
    tracking_number: str,
):
    return (
        db.query(Shipment)
        .filter(Shipment.tracking_number == tracking_number)
        .first()
    )


def get_shipments(
    db: Session,
    current_user,
):
    # Admin, FleetManager and Dispatcher can see all shipments
    if current_user.role.value in ["Admin", "FleetManager", "Dispatcher"]:
        return (
            db.query(Shipment)
            .order_by(Shipment.created_at.desc())
            .all()
        )

    # Driver can see only shipments assigned to them
    if current_user.role.value == "Driver":
        from app.models.driver import Driver

        return (
            db.query(Shipment)
            .join(Driver, Shipment.driver_id == Driver.driver_id)
            .filter(Driver.user_id == current_user.user_id)
            .order_by(Shipment.created_at.desc())
            .all()
        )

    return []

def update_shipment(
    db: Session,
    shipment,
    shipment_data: ShipmentUpdate,
):
    update_data = shipment_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(shipment, field, value)

    db.commit()
    db.refresh(shipment)

    return shipment


def can_transition_shipment_status(
    current_status: ShipmentStatus,
    next_status: ShipmentStatus,
) -> bool:
    return next_status in ALLOWED_STATUS_TRANSITIONS[current_status]


def change_shipment_status(
    db: Session,
    shipment: Shipment,
    next_status: ShipmentStatus,
):
    previous_status = shipment.status
    shipment.status = next_status

    db.commit()
    db.refresh(shipment)

    if previous_status != next_status and next_status in {
        ShipmentStatus.Delivered,
        ShipmentStatus.Delayed,
        ShipmentStatus.Cancelled,
    }:
        if next_status == ShipmentStatus.Delivered:
            title = "Shipment Delivered"
            message = f"Shipment {shipment.tracking_number} has been successfully delivered."
            notification_type = "delivery"
        elif next_status == ShipmentStatus.Delayed:
            title = "Shipment Delayed"
            message = f"Shipment {shipment.tracking_number} has been marked as delayed."
            notification_type = "shipment_status"
        else:
            title = "Shipment Cancelled"
            message = f"Shipment {shipment.tracking_number} has been cancelled."
            notification_type = "shipment_status"

        event_key = f"shipment:{shipment.shipment_id}:{next_status.value}"
        for user_id in operations_user_ids(db):
            create_notification(
                db,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                alert_type=event_key,
            )

    return shipment


def is_driver_assigned_to_shipment(
    db: Session,
    shipment: Shipment,
    user_id: UUID,
) -> bool:
    if shipment.driver_id is None:
        return False

    return (
        db.query(Driver)
        .filter(
            Driver.driver_id == shipment.driver_id,
            Driver.user_id == user_id,
        )
        .first()
        is not None
    )


def delete_shipment(
    db: Session,
    shipment: Shipment,
):
    return change_shipment_status(db, shipment, ShipmentStatus.Cancelled)


def get_shipment_history_by_vehicle(
    db: Session,
    vehicle_id: UUID,
):
    return (
        db.query(Shipment)
        .filter(Shipment.vehicle_id == vehicle_id)
        .order_by(Shipment.created_at.desc())
        .all()
    )
def get_shipment_alerts(db: Session):
    now = datetime.now(timezone.utc)
    approaching_time = now + timedelta(hours=2)

    approaching = (
        db.query(Shipment)
        .filter(
            Shipment.expected_delivery_at != None,
            Shipment.expected_delivery_at >= now,
            Shipment.expected_delivery_at <= approaching_time,
            Shipment.status.notin_(["Delivered", "Cancelled"]),
        )
        .order_by(Shipment.expected_delivery_at.asc())
        .all()
    )

    overdue = (
        db.query(Shipment)
        .filter(
            Shipment.expected_delivery_at != None,
            Shipment.expected_delivery_at < now,
            Shipment.status.notin_(["Delivered", "Cancelled"]),
        )
        .order_by(Shipment.expected_delivery_at.asc())
        .all()
    )

    return {
        "approaching": approaching,
        "overdue": overdue,
    }
def get_shipment_history_by_customer(
    db: Session,
    customer_name: str,
):
    return (
        db.query(Shipment)
        .filter(Shipment.customer_name == customer_name)
        .order_by(Shipment.created_at.desc())
        .all()
    )
