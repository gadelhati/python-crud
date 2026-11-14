from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import BaseConfig, SchemaSoftDelete
from app.schemas.role import RoleResponse
from app.validations.validation import Validation


class UserBase(BaseModel):
    """Base schema for user attributes."""

    username: str = Field(min_length=3, max_length=100)
    email: EmailStr = Field(max_length=100)
    first_name: str | None = Field(default=None, max_length=Validation.NAME_MAX_LENGTH)
    last_name: str | None = Field(default=None, max_length=Validation.NAME_MAX_LENGTH)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return Validation.validate_username(v)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str | None, info) -> str | None:
        return Validation.validate_name(v, info.field_name.replace("_", " ").title())


class UserRequest(UserBase):
    """Schema for user creation and update requests."""

    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool = True
    role_ids: list[UUID] | None = Field(
        default=None,
        max_length=Validation.MAX_ROLES_PER_USER,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None:
            return Validation.validate_password(v)
        return v

    @field_validator("role_ids")
    @classmethod
    def validate_role_ids(cls, v: list[UUID] | None) -> list[UUID] | None:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v

    model_config = BaseConfig.model_config


class UserResponse(SchemaSoftDelete):
    """Schema for user responses."""

    username: str
    email: EmailStr
    first_name: str | None = Field(default=None, max_length=Validation.NAME_MAX_LENGTH)
    last_name: str | None = Field(default=None, max_length=Validation.NAME_MAX_LENGTH)
    is_active: bool
    is_verified: bool
    last_login: datetime | None = None
    roles: list[RoleResponse] = Field(default_factory=list)
