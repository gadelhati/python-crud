# app/models/base.py
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import UUID as UUID_
from sqlalchemy import DateTime, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class IdMixin:
    """Mixin providing a UUID primary key."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(UTC), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(UTC))
    created_by: Mapped[UUID | None] = mapped_column(
        UUID_(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        UUID_(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    deleted_by: Mapped[UUID | None] = mapped_column(
        UUID_(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    version_id: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, doc="Optimistic locking version"
    )


class EntityBase(IdMixin, Base):
    """Base class for entities with a UUID primary key."""

    __abstract__ = True
