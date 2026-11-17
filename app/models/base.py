# app/models/base.py - Base classes and mixins for ORM models
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class IdMixin:
    """Mixin providing a UUID primary key."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)


class TimestampMixin:
    """Mixin providing created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @declared_attr
    def created_by(cls) -> Mapped[UUID | None]:
        return mapped_column(
            Uuid(as_uuid=True),
            ForeignKey("users.id", name=f"fk_{cls.__tablename__}_created_by", use_alter=True),
            nullable=True,
        )

    @declared_attr
    def updated_by(cls) -> Mapped[UUID | None]:
        return mapped_column(
            Uuid(as_uuid=True),
            ForeignKey("users.id", name=f"fk_{cls.__tablename__}_updated_by", use_alter=True),
            nullable=True,
        )

    @declared_attr
    def deleted_by(cls) -> Mapped[UUID | None]:
        return mapped_column(
            Uuid(as_uuid=True),
            ForeignKey("users.id", name=f"fk_{cls.__tablename__}_deleted_by", use_alter=True),
            nullable=True,
        )

    version_id: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, doc="Optimistic locking version"
    )

    @declared_attr.directive
    def __mapper_args__(cls) -> dict:
        return {
            "version_id_col": cls.version_id,
            "version_id_generator": lambda version: (version or 0) + 1,
        }


class EntityBase(Base, IdMixin, TimestampMixin):
    """Base class for entities with a UUID primary key."""

    __abstract__ = True
