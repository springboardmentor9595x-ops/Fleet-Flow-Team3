from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.models.user import RoleEnum


# -------------------------
# Request Schemas
# -------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    role: RoleEnum = RoleEnum.Driver


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    full_name: str
    phone: str | None = None


class EmailUpdate(BaseModel):
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# -------------------------
# Response Schemas
# -------------------------

class UserResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    role: RoleEnum = RoleEnum.Driver
    email_verified: bool

    class Config:
        from_attributes = True


# -------------------------
# JWT Schemas
# -------------------------

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
