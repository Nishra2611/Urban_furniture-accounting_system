from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import UserRole


class SignupRequest(BaseModel):
    login_id: str
    email: EmailStr
    password: str
    re_password: str

    @field_validator("login_id")
    @classmethod
    def validate_login_id(cls, v: str) -> str:
        v = v.strip()
        if not (6 <= len(v) <= 12):
            raise ValueError("Login ID must be between 6 and 12 characters")
        return v


class LoginRequest(BaseModel):
    login_id: str
    password: str

    @field_validator("login_id")
    @classmethod
    def strip_login(cls, v: str) -> str:
        return v.strip()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class CreateUserRequest(BaseModel):
    name: str
    login_id: str
    email: EmailStr
    role: UserRole
    password: str
    re_password: str

    @field_validator("login_id")
    @classmethod
    def validate_login_id(cls, v: str) -> str:
        v = v.strip()
        if not (6 <= len(v) <= 12):
            raise ValueError("Login ID must be between 6 and 12 characters")
        return v


class UserOut(BaseModel):
    id: int
    name: Optional[str]
    login_id: str
    email: EmailStr
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    re_password: str
