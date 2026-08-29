from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db

from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentUpdate,
    ShipmentStatusUpdate,
    
)

from app.crud.shipment import (
    can_transition_shipment_status,
    change_shipment_status,
    create_shipment,
    delete_shipment,
    get_shipment,
    get_shipment_by_tracking_number,
    get_shipments,
    update_shipment,
    get_shipment_history_by_customer,
    get_shipment_history_by_vehicle,
    get_shipment_alerts,
    is_driver_assigned_to_shipment,
)
from app.models.shipment import ShipmentStatus
from app.core.deps import (
    get_current_user,
    require_admin_or_fleet_manager,
    require_shipment_manager,
)


router = APIRouter(
    prefix="/shipments",
    tags=["Shipments"],
)


ROLE_ALLOWED_STATUS_TRANSITIONS = {
    "Admin": None,
    "FleetManager": {
        (ShipmentStatus.Created, ShipmentStatus.Assigned),
        (ShipmentStatus.Created, ShipmentStatus.Cancelled),
        (ShipmentStatus.Assigned, ShipmentStatus.Cancelled),
    },
    "Dispatcher": {
        (ShipmentStatus.Created, ShipmentStatus.Assigned),
        (ShipmentStatus.InTransit, ShipmentStatus.Delayed),
    },
    "Driver": {
        (ShipmentStatus.Assigned, ShipmentStatus.InTransit),
        (ShipmentStatus.InTransit, ShipmentStatus.Delivered),
    },
}


def require_status_transition_permission(db: Session, shipment, next_status: ShipmentStatus, current_user) -> None:
    current_status = ShipmentStatus(shipment.status)
    role = current_user.role.value

    if role not in ROLE_ALLOWED_STATUS_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update shipment status.",
        )

    if not can_transition_shipment_status(current_status, next_status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid shipment status transition: {current_status.value} to {next_status.value}.",
        )

    allowed_transitions = ROLE_ALLOWED_STATUS_TRANSITIONS.get(role)
    if allowed_transitions is not None and (current_status, next_status) not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to make this shipment status change.",
        )

    if role == "Driver" and not is_driver_assigned_to_shipment(db, shipment, current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Drivers can update only shipments assigned to them.",
        )


@router.post(
    "/",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_shipment(
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_shipment_manager),
):
    existing_shipment = get_shipment_by_tracking_number(
        db,
        shipment_data.tracking_number,
        
    )

    if existing_shipment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tracking number already exists",
        )

    return create_shipment(
        db,
        shipment_data,
    )

@router.get(
    "/",
    response_model=list[ShipmentResponse],
)

def get_all_shipments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_shipments(db, current_user)


@router.get(
    "/history/customer/{customer_name}",
    response_model=list[ShipmentResponse],
)


def get_customer_shipment_history(
    customer_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_shipment_manager),
):
    return get_shipment_history_by_customer(
        db,
        customer_name,
    )


@router.get(
    "/history/vehicle/{vehicle_id}",
    response_model=list[ShipmentResponse],
)


def get_vehicle_shipment_history(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_shipment_manager),
):
    return get_shipment_history_by_vehicle(
        db,
        vehicle_id,
    )
@router.get("/alerts")
def shipment_alerts(
    db: Session = Depends(get_db),
    current_user=Depends(require_shipment_manager),
):
    return get_shipment_alerts(db)

@router.patch(
    "/{shipment_id}/status",
    response_model=ShipmentResponse,
)
def update_shipment_status(
    shipment_id: UUID,
    status_data: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    shipment = get_shipment(db, shipment_id)

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    require_status_transition_permission(
        db,
        shipment,
        status_data.status,
        current_user,
    )

    return change_shipment_status(db, shipment, status_data.status)

@router.get(
    "/{shipment_id}",
    response_model=ShipmentResponse,
)

def get_single_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    shipment = get_shipment(db, shipment_id)

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    if current_user.role.value == "Driver" and not is_driver_assigned_to_shipment(
        db,
        shipment,
        current_user.user_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Drivers can view only shipments assigned to them.",
        )

    return shipment


@router.put(
    "/{shipment_id}",
    response_model=ShipmentResponse,
)


def update_existing_shipment(
    shipment_id: UUID,
    shipment_data: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_shipment_manager),
):
    shipment = get_shipment(db, shipment_id)

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    return update_shipment(
        db,
        shipment,
        shipment_data,
    )


@router.delete(
    "/{shipment_id}",
    response_model=ShipmentResponse,
)
def delete_existing_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_fleet_manager),
):
    shipment = get_shipment(db, shipment_id)

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found",
        )

    require_status_transition_permission(
        db,
        shipment,
        ShipmentStatus.Cancelled,
        current_user,
    )

    return delete_shipment(db, shipment)
