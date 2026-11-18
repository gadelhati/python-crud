from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import SchemaBase, SchemaId
from app.schemas.permission import PermissionResponse
from app.validations.role import RoleValidation


class RoleBase(SchemaBase):
    """Base schema for role attributes."""

    name: str = Field(
        min_length=RoleValidation.NAME_MIN_LENGTH, max_length=RoleValidation.NAME_MAX_LENGTH
    )
    description: str | None = Field(default=None, max_length=RoleValidation.DESCRIPTION_MAX_LENGTH)
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        result = RoleValidation.validate_name(v, "Role name")
        if result is None:
            raise ValueError("Role name is required")
        return result

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        return RoleValidation.validate_name(v, "Description")


class RoleRequest(RoleBase):
    """Schema for role creation and update requests."""

    permission_ids: list[UUID] | None = Field(
        default=None,
        max_length=RoleValidation.MAX_PERMISSIONS_PER_ROLE,
    )

    @field_validator("permission_ids")
    @classmethod
    def validate_permission_ids(
        cls,
        v: list[UUID] | None,
    ) -> list[UUID] | None:
        if v is None:
            return v

        if len(v) != len(set(v)):
            raise ValueError("Duplicate permissions not allowed")

        return v


class RoleResponse(RoleBase, SchemaId):
    """Schema for role responses."""

    permissions: list[PermissionResponse] = Field(default_factory=list)
