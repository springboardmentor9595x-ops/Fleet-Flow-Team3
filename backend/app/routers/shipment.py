from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.shipment import Shipment, ShipmentStatus
from app.models.vehicle import Vehicle
from app.models.driver import Driver


router = APIRouter(
    prefix="/shipments",
    tags=["Shipments"],
)


# =========================================================
# SCHEMAS
# =========================================================

class ShipmentCreate(BaseModel):
    tracking_number: str
    source: str
    destination: str
    customer_name: str
    shipment_weight: float
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None


class ShipmentUpdate(BaseModel):
    tracking_number: str | None = None
    source: str | None = None
    destination: str | None = None
    customer_name: str | None = None
    shipment_weight: float | None = None
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus


class ShipmentOut(BaseModel):
    shipment_id: UUID
    tracking_number: str
    source: str
    destination: str
    customer_name: str
    shipment_weight: float
    vehicle_id: UUID | None = None
    driver_id: UUID | None = None
    status: ShipmentStatus

    class Config:
        from_attributes = True


# =========================================================
# GET ALL SHIPMENTS
# =========================================================

@router.get(
    "/",
    response_model=list[ShipmentOut],
)
def get_shipments(
    db: Session = Depends(get_db),
):
    return db.query(Shipment).all()


# =========================================================
# CREATE SHIPMENT
# =========================================================

@router.post(
    "/",
    response_model=ShipmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_shipment(
    shipment_data: ShipmentCreate,
    db: Session = Depends(get_db),
):

    # Validate vehicle if provided
    if shipment_data.vehicle_id is not None:
        vehicle = (
            db.query(Vehicle)
            .filter(Vehicle.vehicle_id == shipment_data.vehicle_id)
            .first()
        )

        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found",
            )

    # Validate driver if provided
    if shipment_data.driver_id is not None:
        driver = (
            db.query(Driver)
            .filter(Driver.driver_id == shipment_data.driver_id)
            .first()
        )

        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Driver not found",
            )

    # Default status
    shipment_status = ShipmentStatus.Created

    # If both vehicle and driver are provided,
    # shipment is automatically assigned
    if (
        shipment_data.vehicle_id is not None
        and shipment_data.driver_id is not None
    ):
        shipment_status = ShipmentStatus.Assigned

    shipment = Shipment(
        tracking_number=shipment_data.tracking_number,
        source=shipment_data.source,
        destination=shipment_data.destination,
        customer_name=shipment_data.customer_name,
        shipment_weight=shipment_data.shipment_weight,
        vehicle_id=shipment_data.vehicle_id,
        driver_id=shipment_data.driver_id,
        status=shipment_status,
    )

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    return shipment


# =========================================================
# GET SINGLE SHIPMENT
# =========================================================

@router.get(
    "/{shipment_id}",
    response_model=ShipmentOut,
)
def get_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
):

    shipment = (
        db.query(Shipment)
        .filter(Shipment.shipment_id == shipment_id)
        .first()
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    return shipment


# =========================================================
# UPDATE SHIPMENT
# =========================================================

@router.put(
    "/{shipment_id}",
    response_model=ShipmentOut,
)
def update_shipment(
    shipment_id: UUID,
    shipment_data: ShipmentUpdate,
    db: Session = Depends(get_db),
):

    shipment = (
        db.query(Shipment)
        .filter(Shipment.shipment_id == shipment_id)
        .first()
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    # -----------------------------------------
    # Update basic shipment information
    # -----------------------------------------

    if shipment_data.tracking_number is not None:
        shipment.tracking_number = shipment_data.tracking_number

    if shipment_data.source is not None:
        shipment.source = shipment_data.source

    if shipment_data.destination is not None:
        shipment.destination = shipment_data.destination

    if shipment_data.customer_name is not None:
        shipment.customer_name = shipment_data.customer_name

    if shipment_data.shipment_weight is not None:
        shipment.shipment_weight = shipment_data.shipment_weight

    # -----------------------------------------
    # Validate and update vehicle
    # -----------------------------------------

    if shipment_data.vehicle_id is not None:

        vehicle = (
            db.query(Vehicle)
            .filter(Vehicle.vehicle_id == shipment_data.vehicle_id)
            .first()
        )

        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail="Vehicle not found",
            )

        shipment.vehicle_id = shipment_data.vehicle_id

    # -----------------------------------------
    # Validate and update driver
    # -----------------------------------------

    if shipment_data.driver_id is not None:

        driver = (
            db.query(Driver)
            .filter(Driver.driver_id == shipment_data.driver_id)
            .first()
        )

        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Driver not found",
            )

        shipment.driver_id = shipment_data.driver_id

    # -----------------------------------------
    # Automatically assign shipment
    # -----------------------------------------

    if (
        shipment.vehicle_id is not None
        and shipment.driver_id is not None
    ):
        shipment.status = ShipmentStatus.Assigned

    db.commit()
    db.refresh(shipment)

    return shipment


# =========================================================
# UPDATE SHIPMENT STATUS
# =========================================================

@router.patch(
    "/{shipment_id}/status",
    response_model=ShipmentOut,
)
def update_shipment_status(
    shipment_id: UUID,
    status_data: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
):

    shipment = (
        db.query(Shipment)
        .filter(Shipment.shipment_id == shipment_id)
        .first()
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    shipment.status = status_data.status

    db.commit()
    db.refresh(shipment)

    return shipment


# =========================================================
# DELETE SHIPMENT
# =========================================================

@router.delete(
    "/{shipment_id}",
)
def delete_shipment(
    shipment_id: UUID,
    db: Session = Depends(get_db),
):

    shipment = (
        db.query(Shipment)
        .filter(Shipment.shipment_id == shipment_id)
        .first()
    )

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    db.delete(shipment)
    db.commit()

    return {
        "message": "Shipment deleted successfully"
    }