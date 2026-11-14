from __future__ import annotations

from pydantic import BaseModel

from app.enum.permission_action import EnumPermissionAction
from app.schemas.base import (
    SchemaSoftDelete,
)


class PermissionBase(BaseModel):
    """Base schema for permission attributes."""

    name: str
    description: str | None = None
    action: EnumPermissionAction


class PermissionRequest(PermissionBase):
    """Schema for permission creation and update requests."""

    pass


class PermissionResponse(SchemaSoftDelete):
    """Schema for permission responses."""

    name: str
    description: str | None = None
    action: EnumPermissionAction
