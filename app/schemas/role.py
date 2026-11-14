from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseConfig, SchemaSoftDelete
from app.schemas.permission import PermissionResponse
from app.validations.validation import Validation


class RoleBase(BaseModel):
    """Base schema for role attributes."""

    name: str
    description: str | None = None
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        result = Validation.validate_name(v, "Role name")
        if result is None:
            raise ValueError("Role name is required")
        return result

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        return Validation.validate_name(v, "Description")


class RoleRequest(RoleBase):
    """Schema for role creation and update requests."""

    permission_ids: list[UUID] | None = Field(
        default=None,
        max_length=Validation.MAX_PERMISSIONS_PER_ROLE,
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

    model_config = BaseConfig.model_config


class RoleResponse(SchemaSoftDelete):
    """Schema for role responses."""

    name: str
    description: str | None = None
    is_default: bool
    permissions: list[PermissionResponse] = Field(default_factory=list)
