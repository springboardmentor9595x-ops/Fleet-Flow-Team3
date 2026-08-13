from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.attendance import Attendance
from app.core.deps import get_current_user

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


class AttendanceCreate(BaseModel):
    driver_id: UUID | None = None


class AttendanceOut(BaseModel):
    attendance_id: UUID
    driver_id: UUID | None

    class Config:
        from_attributes = True


# GET ALL ATTENDANCE RECORDS
@router.get(
    "/",
    response_model=list[AttendanceOut],
)
def get_attendance_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Attendance).all()


# CREATE ATTENDANCE RECORD
@router.post(
    "/",
    response_model=AttendanceOut,
    status_code=status.HTTP_201_CREATED,
)
def create_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    attendance = Attendance(
        driver_id=attendance_data.driver_id,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance


# GET SINGLE ATTENDANCE RECORD
@router.get(
    "/{attendance_id}",
    response_model=AttendanceOut,
)
def get_attendance(
    attendance_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    attendance = (
        db.query(Attendance)
        .filter(Attendance.attendance_id == attendance_id)
        .first()
    )

    if not attendance:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found",
        )

    return attendance


# DELETE ATTENDANCE RECORD
@router.delete(
    "/{attendance_id}",
)
def delete_attendance(
    attendance_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    attendance = (
        db.query(Attendance)
        .filter(Attendance.attendance_id == attendance_id)
        .first()
    )

    if not attendance:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found",
        )

    db.delete(attendance)
    db.commit()

    return {
        "message": "Attendance record deleted successfully"
    }