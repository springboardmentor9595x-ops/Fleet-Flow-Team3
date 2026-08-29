from sqlalchemy.orm import Session

from app.models.gps_tracking import GPSTracking
from app.schemas.gps_tracking import GPSLocationCreate


def create_gps_location(
    db: Session,
    gps_data: GPSLocationCreate,
):
    gps_location = GPSTracking(
        vehicle_id=gps_data.vehicle_id,
        latitude=gps_data.latitude,
        longitude=gps_data.longitude,
        speed=gps_data.speed,
    )

    db.add(gps_location)
    db.commit()
    db.refresh(gps_location)

    return gps_location
def get_latest_gps_location(
    db: Session,
    vehicle_id,
):
    locations = get_latest_gps_locations(db, vehicle_id)
    return locations[0] if locations else None


def get_latest_gps_locations(
    db: Session,
    vehicle_id,
    limit: int = 2,
):
    """Return the newest persisted locations, newest record first."""
    return (
        db.query(GPSTracking)
        .filter(GPSTracking.vehicle_id == vehicle_id)
        .order_by(GPSTracking.recorded_time.desc(), GPSTracking.gps_id.desc())
        .limit(limit)
        .all()
    )
