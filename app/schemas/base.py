from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseConfig:
    """Base configuration for all schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class SchemaBase(BaseModel):
    """Base schema for all application schemas."""

    model_config = BaseConfig.model_config


class SchemaAudit(SchemaBase):
    """Schema containing entity identification and audit fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None
    version_id: int = Field(
        ge=1,
        description="Optimistic locking version",
        examples=[1],
    )


class SchemaSoftDelete(SchemaAudit):
    """Schema containing audit and soft delete fields."""

    deleted_at: datetime | None = None
    deleted_by: UUID | None = None


class DTOPagination(SchemaBase):
    """Schema for paginated responses."""

    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(default=1, ge=1, description="Current page")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class ValidationError(SchemaBase):
    """Schema for validation error details."""

    field: str
    rejected_value: str
    message: str


class ResponseError(SchemaBase):
    """Schema for error responses."""

    code: int
    status: str
    message: str
    validation_errors: list[ValidationError] | None = None


class SchemaSwagger(SchemaBase):
    """Schema for Swagger authentication examples."""

    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)
