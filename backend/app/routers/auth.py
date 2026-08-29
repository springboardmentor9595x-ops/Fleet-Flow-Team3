from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.core.deps import get_current_user,RoleChecker
from send_email import send_verification_email
from database import get_db

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    ProfileUpdate,
    EmailUpdate,
    PasswordChange,
    EmailVerificationRequest,
    ResendVerificationRequest,
)

from app.crud.user import (
    create_user,
    get_user_by_email,
    authenticate_user,
    update_user_profile,
    update_user_email,
    update_user_password,
    set_verification_code,
    verify_user_email,
)

from app.core.security import (create_access_token,verify_password)
from app.models.user import RoleEnum

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

VERIFICATION_CODE_LIFETIME_MINUTES = 10


def create_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


async def create_and_send_verification_code(db: Session, user) -> None:
    code = create_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=VERIFICATION_CODE_LIFETIME_MINUTES
    )
    set_verification_code(db, user, hash_verification_code(code), expires_at)
    await send_verification_email(user.email, user.full_name, code)


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def signup(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    # Public registration is never a role-management endpoint. It can create
    # a Driver account only; privileged accounts require controlled provision.
    if user.role != RoleEnum.Driver:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration can create only Driver accounts.",
        )

    existing_user = get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = create_user(db, user)

    try:
        await create_and_send_verification_code(db, new_user)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account created, but the verification email could not be sent. Please try again shortly.",
        ) from error

    return new_user


@router.post("/verify-email", response_model=UserResponse)
def verify_email(
    verification: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, verification.email)
    if not user or not user.verification_code_hash:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    expires_at = user.verification_code_expires_at
    if not expires_at or expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="This verification code has expired. Request a new one.",
        )

    if not secrets.compare_digest(
        hash_verification_code(verification.code),
        user.verification_code_hash,
    ):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    return verify_user_email(db, user)


@router.post("/resend-verification")
async def resend_verification_email(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, request.email)
    if not user:
        return {"message": "If an account exists for this email, a verification code has been sent."}

    if user.email_verified:
        raise HTTPException(status_code=400, detail="This email is already verified. Please sign in.")

    try:
        await create_and_send_verification_code(db, user)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send a verification email right now. Check the mail settings and try again.",
        ) from error

    return {"message": "A new verification code has been sent to your email."}


@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    authenticated_user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not authenticated_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before signing in.",
        )

    access_token = create_access_token(
        data={
            "sub": authenticated_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
@router.get(
    "/me",
    response_model=UserResponse
)
def read_users_me(
    current_user=Depends(get_current_user)
):
    return current_user
@router.put("/me", response_model=UserResponse)
def update_my_profile(
    profile: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_user_profile(
        db,
        current_user,
        profile.full_name,
        profile.phone,
    )


@router.put("/me/email", response_model=UserResponse)
def update_my_email(
    email_data: EmailUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    existing_user = get_user_by_email(db, email_data.email)

    if existing_user and existing_user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return update_user_email(db, current_user, email_data.email)


@router.put("/me/password")
def change_my_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not verify_password(
        password_data.current_password,
        current_user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must contain at least 8 characters",
        )

    update_user_password(
        db,
        current_user,
        password_data.new_password,
    )

    return {"message": "Password updated successfully"}
