from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


def _validate_password_strength(password: str) -> str:
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise ValueError("Password must include at least one letter and one number")
    return password


class SignUpRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class MessageOut(BaseModel):
    message: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatar_emoji: str = "🌸"
    trial_started_at: datetime
    trial_ends_at: datetime
    subscription_status: str = "trialing"
    subscription_tier: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
