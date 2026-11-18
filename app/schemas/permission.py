from __future__ import annotations

from pydantic import Field

from app.enum.permission_action import EnumPermissionAction
from app.schemas.base import SchemaAudit, SchemaBase, SchemaId
from app.validations.permission import PermissionValidation


class PermissionBase(SchemaBase):
    """Base schema for permission attributes."""

    name: str = Field(
        min_length=PermissionValidation.NAME_MIN_LENGTH,
        max_length=PermissionValidation.NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None, max_length=PermissionValidation.DESCRIPTION_MAX_LENGTH
    )
    action: EnumPermissionAction


class PermissionRequest(PermissionBase):
    """Schema for permission creation and update requests."""


class PermissionResponse(PermissionBase, SchemaId):
    """Schema for permission responses."""


class PermissionResponseAudit(PermissionBase, SchemaAudit):
    """Schema for permission responses with audiction."""
