from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.core.security import verify_token
from app.crud.user import get_user_by_email


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    
    """
    Get the currently authenticated user.
    """

    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    email = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = get_user_by_email(db, email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def role_value(current_user) -> str:
    """Return the persisted role value for SQLAlchemy/Pydantic enum objects."""
    return getattr(current_user.role, "value", current_user.role)


class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(get_current_user)
    ):
        if role_value(current_user) not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action."
            )

        return current_user
    # Role-based dependencies

require_admin = RoleChecker(["Admin"])

require_admin_or_fleet_manager = RoleChecker(
    ["Admin", "FleetManager"]
)

require_dispatcher = RoleChecker(["Dispatcher"])
require_shipment_manager = RoleChecker(
    ["Admin", "FleetManager", "Dispatcher"]
)

require_driver = RoleChecker(["Driver"])

# Dashboard categories have deliberately different audiences.  Centralising
# these checks prevents router-specific role lists from drifting apart.
require_fleet_analytics = RoleChecker(["Admin", "FleetManager"])
require_logistics_analytics = RoleChecker(["Admin", "FleetManager", "Dispatcher"])
