from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.trip import Trip, TripStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


def get_maintenance(db: Session, maintenance_id: UUID) -> Maintenance | None:
    return db.query(Maintenance).filter(Maintenance.maintenance_id == maintenance_id).first()


def get_maintenance_list(db: Session) -> list[Maintenance]:
    return db.query(Maintenance).order_by(Maintenance.service_date.desc()).all()


def get_vehicle_maintenance(db: Session, vehicle_id: UUID) -> list[Maintenance]:
    return db.query(Maintenance).filter(Maintenance.vehicle_id == vehicle_id).order_by(Maintenance.service_date.desc()).all()


def vehicle_has_active_trip(db: Session, vehicle_id: UUID) -> bool:
    return db.query(Trip).filter(Trip.vehicle_id == vehicle_id, Trip.status == TripStatus.Active).first() is not None


def create_maintenance(db: Session, payload: MaintenanceCreate) -> Maintenance:
    maintenance = Maintenance(**payload.model_dump())
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return maintenance


def _apply_vehicle_status(db: Session, maintenance: Maintenance, previous_status: MaintenanceStatus | None = None) -> None:
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == maintenance.vehicle_id).first()
    if vehicle is None:
        return
    if maintenance.status == MaintenanceStatus.InProgress:
        if vehicle_has_active_trip(db, maintenance.vehicle_id):
            raise ValueError("Cannot start maintenance while the vehicle has an active trip.")
        vehicle.status = VehicleStatus.Maintenance
        maintenance.started_at = maintenance.started_at or datetime.now(timezone.utc)
    elif maintenance.status in {MaintenanceStatus.Completed, MaintenanceStatus.Resolved}:
        maintenance.completed_at = maintenance.completed_at or datetime.now(timezone.utc)
        vehicle.status = VehicleStatus.Available
    elif maintenance.status == MaintenanceStatus.Cancelled and previous_status == MaintenanceStatus.InProgress:
        vehicle.status = VehicleStatus.Available


def update_maintenance(db: Session, maintenance: Maintenance, payload: MaintenanceUpdate) -> Maintenance:
    values = payload.model_dump(exclude_unset=True)
    previous_status = maintenance.status
    for field, value in values.items():
        setattr(maintenance, field, value)
    _apply_vehicle_status(db, maintenance, previous_status)
    db.commit()
    db.refresh(maintenance)
    return maintenance


def delete_maintenance(db: Session, maintenance: Maintenance) -> None:
    if maintenance.status == MaintenanceStatus.InProgress:
        raise ValueError("In-progress maintenance cannot be deleted. Complete or cancel it first.")
    db.delete(maintenance)
    db.commit()


def get_upcoming_and_overdue(db: Session) -> tuple[list[Maintenance], list[Maintenance]]:
    now = datetime.now(timezone.utc)
    next_week = now + timedelta(days=7)
    active_statuses = [MaintenanceStatus.Scheduled, MaintenanceStatus.InProgress]
    # Scheduled work is due on service_date. next_service_date remains the
    # post-service planning field and is not used for active reminders.
    upcoming = db.query(Maintenance).filter(Maintenance.service_date >= now, Maintenance.service_date <= next_week, Maintenance.status.in_(active_statuses)).order_by(Maintenance.service_date.asc()).all()
    overdue = db.query(Maintenance).filter(Maintenance.service_date < now, Maintenance.status.in_(active_statuses)).order_by(Maintenance.service_date.asc()).all()
    return upcoming, overdue
