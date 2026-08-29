from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud.attendance import create_activity, get_driver_activity, get_open_check_in
from app.crud.driver import get_driver_by_user_id
from app.models.attendance import AttendanceActivityType
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from database import get_db


router = APIRouter(prefix="/attendance", tags=["Driver Attendance & Activity"])


def current_driver_or_404(db: Session, current_user):
    record = get_driver_by_user_id(db, current_user.user_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")
    return record[0]


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(payload: AttendanceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Driver users can check in.")
    driver = current_driver_or_404(db, current_user)
    if get_open_check_in(db, driver.driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver already has an open check-in.")
    return create_activity(db, driver_id=driver.driver_id, activity_type=AttendanceActivityType.CheckIn, notes=payload.notes)


@router.post("/check-out", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_out(payload: AttendanceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Driver users can check out.")
    driver = current_driver_or_404(db, current_user)
    if not get_open_check_in(db, driver.driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver must check in before checking out.")
    return create_activity(db, driver_id=driver.driver_id, activity_type=AttendanceActivityType.CheckOut, notes=payload.notes)


@router.get("/me", response_model=list[AttendanceResponse])
def get_my_activity(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Driver users can access this endpoint.")
    driver = current_driver_or_404(db, current_user)
    return get_driver_activity(db, driver.driver_id)


@router.get("/driver/{driver_id}", response_model=list[AttendanceResponse])
def get_activity_for_driver(driver_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return get_driver_activity(db, driver_id)
    if current_user.role.value == "Driver":
        driver = current_driver_or_404(db, current_user)
        if driver.driver_id == driver_id:
            return get_driver_activity(db, driver_id)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this driver activity.")
