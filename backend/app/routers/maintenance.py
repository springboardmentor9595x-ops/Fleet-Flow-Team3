from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin_or_fleet_manager
from app.crud.driver import get_driver_by_user_id
from app.crud.maintenance import (
    create_maintenance,
    delete_maintenance,
    get_maintenance,
    get_maintenance_list,
    get_upcoming_and_overdue,
    get_vehicle_maintenance,
    update_maintenance,
)
from app.models.vehicle import Vehicle
from app.schemas.maintenance import MaintenanceAlertsResponse, MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate
from database import get_db


router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


def require_vehicle_access(db: Session, vehicle_id: UUID, current_user) -> None:
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return
    driver_row = get_driver_by_user_id(db, current_user.user_id)
    driver = driver_row[0] if driver_row else None
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if driver is None or vehicle is None or vehicle.assigned_driver != driver.driver_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Drivers can view maintenance only for their assigned vehicle.")


@router.post("/", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def schedule_maintenance(payload: MaintenanceCreate, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    if not db.query(Vehicle).filter(Vehicle.vehicle_id == payload.vehicle_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return create_maintenance(db, payload)


@router.get("/upcoming", response_model=MaintenanceAlertsResponse)
def maintenance_alerts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    upcoming, overdue = get_upcoming_and_overdue(db)
    if current_user.role.value == "Driver":
        driver_row = get_driver_by_user_id(db, current_user.user_id)
        driver = driver_row[0] if driver_row else None
        if driver is None:
            return {"upcoming": [], "overdue": []}
        vehicle_ids = {vehicle.vehicle_id for vehicle in db.query(Vehicle).filter(Vehicle.assigned_driver == driver.driver_id).all()}
        upcoming = [item for item in upcoming if item.vehicle_id in vehicle_ids]
        overdue = [item for item in overdue if item.vehicle_id in vehicle_ids]
    return {"upcoming": upcoming, "overdue": overdue}


@router.get("/vehicle/{vehicle_id}", response_model=list[MaintenanceResponse])
def vehicle_maintenance(vehicle_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_vehicle_access(db, vehicle_id, current_user)
    return get_vehicle_maintenance(db, vehicle_id)


@router.get("/", response_model=list[MaintenanceResponse])
def list_maintenance(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        return get_maintenance_list(db)
    driver_row = get_driver_by_user_id(db, current_user.user_id)
    driver = driver_row[0] if driver_row else None
    if driver is None:
        return []
    vehicle_ids = [vehicle.vehicle_id for vehicle in db.query(Vehicle).filter(Vehicle.assigned_driver == driver.driver_id).all()]
    return [item for item in get_maintenance_list(db) if item.vehicle_id in vehicle_ids]


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_single_maintenance(maintenance_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    maintenance = get_maintenance(db, maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    require_vehicle_access(db, maintenance.vehicle_id, current_user)
    return maintenance


@router.put("/{maintenance_id}", response_model=MaintenanceResponse)
def edit_maintenance(maintenance_id: UUID, payload: MaintenanceUpdate, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    maintenance = get_maintenance(db, maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    try:
        return update_maintenance(db, maintenance, payload)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.delete("/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_maintenance(maintenance_id: UUID, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    maintenance = get_maintenance(db, maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    try:
        delete_maintenance(db, maintenance)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
