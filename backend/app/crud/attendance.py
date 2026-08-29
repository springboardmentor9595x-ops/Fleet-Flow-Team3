from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceActivityType


def create_activity(db: Session, *, driver_id, activity_type: AttendanceActivityType, trip_id=None, notes: str | None = None, commit: bool = True) -> Attendance:
    activity = Attendance(driver_id=driver_id, activity_type=activity_type, trip_id=trip_id, notes=notes)
    db.add(activity)
    if commit:
        db.commit()
        db.refresh(activity)
    return activity


def get_driver_activity(db: Session, driver_id, limit: int = 50) -> list[Attendance]:
    return db.query(Attendance).filter(Attendance.driver_id == driver_id).order_by(Attendance.occurred_at.desc(), Attendance.attendance_id.desc()).limit(limit).all()


def get_open_check_in(db: Session, driver_id) -> Attendance | None:
    latest = db.query(Attendance).filter(Attendance.driver_id == driver_id, Attendance.activity_type.in_([AttendanceActivityType.CheckIn, AttendanceActivityType.CheckOut])).order_by(Attendance.occurred_at.desc(), Attendance.attendance_id.desc()).first()
    return latest if latest and latest.activity_type == AttendanceActivityType.CheckIn else None
