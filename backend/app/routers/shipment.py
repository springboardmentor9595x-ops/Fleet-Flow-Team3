from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentOut,
)

from app.crud.shipment import (
    create_shipment,
    get_shipments,
    get_shipment,
    update_shipment,
    delete_shipment,
)

from app.core.deps import get_current_user, require_roles

from app.models.user import User, RoleEnum
from app.models.driver import Driver


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/shipments",
    tags=["Shipments"],
)


# ============================================================
# CREATE SHIPMENT
# Admin / FleetManager / Dispatcher
# ============================================================

@router.post(
    "/",
    response_model=ShipmentOut,
    status_code=201,
)
def create_shipment_api(
    shipment_in: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.Admin,
            RoleEnum.FleetManager,
            RoleEnum.Dispatcher,
        )
    ),
):
    return create_shipment(
        db=db,
        tracking_number=shipment_in.tracking_number,
        source=shipment_in.source,
        destination=shipment_in.destination,
        customer_name=shipment_in.customer_name,
        shipment_weight=shipment_in.shipment_weight,
        vehicle_id=shipment_in.vehicle_id,
        driver_id=shipment_in.driver_id,
        status=shipment_in.status,
    )


# ============================================================
# GET ALL SHIPMENTS — scoped by role
# Admin / FleetManager / Dispatcher: all
# Driver: only their own (via driver profile)
# ============================================================

@router.get(
    "/",
    response_model=list[ShipmentOut],
)
def get_shipments_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # If Driver: find their driver profile, return only their shipments
    if current_user.role == RoleEnum.Driver or str(current_user.role) == "Driver":
        driver = (
            db.query(Driver)
            .filter(Driver.user_id == current_user.user_id)
            .first()
        )
        if not driver:
            return []
        from app.models.shipment import Shipment
        return (
            db.query(Shipment)
            .filter(Shipment.driver_id == driver.driver_id)
            .all()
        )

    # Admin / FleetManager / Dispatcher: all shipments
    return get_shipments(db)


# ============================================================
# GET ONE SHIPMENT
# Admin / FleetManager / Dispatcher: any
# Driver: only their own
# ============================================================

@router.get(
    "/{shipment_id}",
    response_model=ShipmentOut,
)
def get_shipment_api(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shipment = get_shipment(db, shipment_id)

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Driver: can only view their own
    if current_user.role == RoleEnum.Driver or str(current_user.role) == "Driver":
        driver = (
            db.query(Driver)
            .filter(Driver.user_id == current_user.user_id)
            .first()
        )
        if not driver or str(shipment.driver_id) != str(driver.driver_id):
            raise HTTPException(status_code=403, detail="You can only view your own shipments")

    return shipment


# ============================================================
# UPDATE SHIPMENT
# Admin / FleetManager / Dispatcher
# ============================================================

@router.put(
    "/{shipment_id}",
    response_model=ShipmentOut,
)
def update_shipment_api(
    shipment_id: UUID,
    shipment_in: ShipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.Admin,
            RoleEnum.FleetManager,
            RoleEnum.Dispatcher,
        )
    ),
):
    shipment = get_shipment(db, shipment_id)

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    update_shipment(
        db=db,
        shipment=shipment,
        tracking_number=shipment_in.tracking_number,
        source=shipment_in.source,
        destination=shipment_in.destination,
        customer_name=shipment_in.customer_name,
        shipment_weight=shipment_in.shipment_weight,
        vehicle_id=shipment_in.vehicle_id,
        driver_id=shipment_in.driver_id,
        status=shipment_in.status,
    )

    return shipment


# ============================================================
# DELETE SHIPMENT
# Admin only (hard delete); Dispatcher/FM use status=Cancelled
# ============================================================

@router.delete(
    "/{shipment_id}",
)
def delete_shipment_api(
    shipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleEnum.Admin)
    ),
):
    shipment = get_shipment(db, shipment_id)

    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    delete_shipment(db, shipment)

    return {"message": "Shipment deleted successfully"}