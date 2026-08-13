from sqlalchemy.orm import Session

from app.models.driver import Driver


# ============================================================
# CREATE DRIVER
# ============================================================

def create_driver(
    db: Session,
    user_id=None,
):

    driver = Driver(
        user_id=user_id,
    )

    db.add(driver)

    db.commit()

    db.refresh(driver)

    return driver


# ============================================================
# GET ALL DRIVERS
# ============================================================

def get_drivers(
    db: Session,
):

    return (
        db.query(Driver)
        .all()
    )


# ============================================================
# GET ONE DRIVER
# ============================================================

def get_driver(
    db: Session,
    driver_id,
):

    return (
        db.query(Driver)
        .filter(
            Driver.driver_id == driver_id
        )
        .first()
    )


# ============================================================
# UPDATE DRIVER
# ============================================================

def update_driver(
    db: Session,
    driver,
    user_id=None,
):

    driver.user_id = user_id

    db.commit()

    db.refresh(driver)

    return driver


# ============================================================
# DELETE DRIVER
# ============================================================

def delete_driver(
    db: Session,
    driver,
):

    db.delete(driver)

    db.commit()

    return True