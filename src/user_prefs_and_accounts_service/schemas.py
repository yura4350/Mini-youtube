import re
from typing import List, Optional

from pydantic import BaseModel, field_validator
from .config import PASSWORD_MIN_LENGTH



"""
Pydantic Models (Dataclass). Definitions of API Models
"""


def validate_password_strength(password: str) -> str:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters."
        )
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must include at least one letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must include at least one number.")
    return password


class UserCreate(BaseModel):
    name: str
    email: str
    role: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    bio: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class PublicUserResponse(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserPreferencesResponse(BaseModel):
    user_id: int
    privacy: str
    notifications: bool
    ui_theme: str

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    privacy: Optional[str] = None
    notifications: Optional[bool] = None
    ui_theme: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)