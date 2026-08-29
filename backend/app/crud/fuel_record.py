from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.fuel_record import FuelRecord
from app.schemas.fuel_record import FuelRecordCreate, FuelRecordUpdate


def _next_fuel_reference(db: Session) -> str:
    latest = (
        db.query(FuelRecord.fuel_reference)
        .filter(FuelRecord.fuel_reference.isnot(None))
        .order_by(FuelRecord.fuel_reference.desc())
        .first()
    )
    try:
        sequence = int(latest[0].split("-")[-1]) + 1 if latest else 1
    except (AttributeError, ValueError):
        sequence = 1
    return f"FUEL-{sequence:04d}"


def create_fuel_record(db: Session, payload: FuelRecordCreate) -> FuelRecord:
    # The unique database index is the final concurrency guard. Retrying with
    # a fresh reference handles a simultaneous insert safely.
    for _ in range(3):
        record = FuelRecord(**payload.model_dump(), fuel_reference=_next_fuel_reference(db))
        db.add(record)
        try:
            db.commit()
            db.refresh(record)
            return record
        except IntegrityError:
            db.rollback()
    raise RuntimeError("Unable to allocate a unique fuel reference. Please retry.")


def get_fuel_record(db: Session, fuel_id: UUID) -> FuelRecord | None:
    return db.query(FuelRecord).filter(FuelRecord.fuel_id == fuel_id).first()


def get_fuel_records(db: Session, vehicle_id: UUID | None = None) -> list[FuelRecord]:
    query = db.query(FuelRecord)
    if vehicle_id is not None:
        query = query.filter(FuelRecord.vehicle_id == vehicle_id)
    return query.order_by(FuelRecord.refill_date.desc(), FuelRecord.fuel_id.desc()).all()


def update_fuel_record(db: Session, record: FuelRecord, payload: FuelRecordUpdate) -> FuelRecord:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


def delete_fuel_record(db: Session, record: FuelRecord) -> None:
    db.delete(record)
    db.commit()
