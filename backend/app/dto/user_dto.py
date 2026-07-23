"""Data shapes for user accounts."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.dto.common_dto import ORM_CONFIG
from app.models.enums import Role


class UserBase(BaseModel):
    """Fields common to creating and reading a user."""

    email: EmailStr
    full_name: str
    role: Role = Role.viewer
    is_active: bool = True


class UserCreateRequest(UserBase):
    """Incoming payload when an admin adds an account."""

    password: str = Field(min_length=6)


class UserUpdateRequest(BaseModel):
    """Every field optional: only what is sent gets changed."""

    full_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)


class UserResponse(UserBase):
    """Outgoing shape. Note the password hash is never included."""

    model_config = ORM_CONFIG

    id: int
    created_at: Optional[datetime] = None
