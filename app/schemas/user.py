from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.schemas.base import SchemaAudit, SchemaBase, SchemaId
from app.schemas.role import RoleResponse
from app.validations.user import UserValidation


class UserBase(SchemaBase):
    """Base schema for user attributes."""

    username: str = Field(
        min_length=UserValidation.USERNAME_MIN_LENGTH,
        max_length=UserValidation.USERNAME_MAX_LENGTH,
    )
    email: EmailStr = Field(
        min_length=UserValidation.EMAIL_MIN_LENGTH,
        max_length=UserValidation.EMAIL_MAX_LENGTH,
    )
    first_name: str | None = Field(
        default=None,
        min_length=UserValidation.NAME_MIN_LENGTH,
        max_length=UserValidation.NAME_MAX_LENGTH,
    )
    last_name: str | None = Field(
        default=None,
        min_length=UserValidation.NAME_MIN_LENGTH,
        max_length=UserValidation.NAME_MAX_LENGTH,
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return UserValidation.validate_username(v)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v: str | None, info) -> str | None:
        return UserValidation.validate_names(v, info.field_name.replace("_", " ").title())


class UserRequest(UserBase):
    """Schema for user creation and update requests without password."""

    is_active: bool = True


class UserPasswordRequest(SchemaBase):
    """Schema for user creation and update requests."""

    password: str = Field(
        min_length=UserValidation.PASSWORD_MIN_LENGTH,
        max_length=UserValidation.PASSWORD_MAX_LENGTH,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None:
            return UserValidation.validate_password(v)
        return v

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=False,
        validate_assignment=True,
    )


class UserRoleRequest(SchemaBase):
    """Schema for user creation and update requests without password."""

    role_ids: list[UUID] | None = Field(
        default=None,
        min_length=UserValidation.MIN_ROLES_PER_USER,
        max_length=UserValidation.MAX_ROLES_PER_USER,
    )

    @field_validator("role_ids")
    @classmethod
    def validate_role_ids(cls, v: list[UUID] | None) -> list[UUID] | None:
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Duplicate roles not allowed")
        return v


class UserResponse(UserBase, SchemaId):
    """Schema for user responses."""

    is_active: bool
    is_verified: bool
    last_login: datetime | None = None
    roles: list[RoleResponse] = Field(default_factory=list)


class UserResponseAudit(UserResponse, SchemaAudit):
    """Schema for user responses with audiction."""
