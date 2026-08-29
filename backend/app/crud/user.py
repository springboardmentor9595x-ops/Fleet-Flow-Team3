from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user by email.
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    """
    Create a new user with a hashed password.
    """

    hashed_pw = hash_password(user.password)

    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hashed_pw,
        phone=user.phone,
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate a user during login.
    """

    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user
def update_user_profile(db: Session, user: User, full_name: str, phone: str | None):
    user.full_name = full_name
    user.phone = phone

    db.commit()
    db.refresh(user)

    return user


def update_user_email(db: Session, user: User, email: str):
    user.email = email

    db.commit()
    db.refresh(user)

    return user


def update_user_password(db: Session, user: User, new_password: str):
    user.password = hash_password(new_password)

    db.commit()
    db.refresh(user)

    return user


def set_verification_code(
    db: Session,
    user: User,
    code_hash: str,
    expires_at: datetime,
):
    user.email_verified = False
    user.verification_code_hash = code_hash
    user.verification_code_expires_at = expires_at
    db.commit()
    db.refresh(user)
    return user


def verify_user_email(db: Session, user: User):
    user.email_verified = True
    user.verification_code_hash = None
    user.verification_code_expires_at = None
    db.commit()
    db.refresh(user)
    return user
