# app/repository/base.py
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.base import EntityBase


class BaseRepository[T: EntityBase]:
    """Generic repository for entities with a UUID primary key.

    Never commits: the service controls the transaction.
    """

    model: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    def _select(self, *, include_deleted: bool = False) -> Select[tuple[T]]:
        """Base query. Subclasses override it to add default filters."""
        return select(self.model)

    def find_all(
        self, *, offset: int = 0, limit: int = 100, include_deleted: bool = False
    ) -> Sequence[T]:
        stmt = (
            self._select(include_deleted=include_deleted)
            .order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def count(self, *, include_deleted: bool = False) -> int:
        stmt = (
            self._select(include_deleted=include_deleted)
            .with_only_columns(func.count(self.model.id), maintain_column_froms=True)
            .order_by(None)
        )
        return self.db.scalar(stmt) or 0

    def find_by_id(self, id: UUID, *, include_deleted: bool = False) -> T | None:
        stmt = self._select(include_deleted=include_deleted).where(self.model.id == id)
        return self.db.scalar(stmt)

    def find_by_ids(self, ids: Sequence[UUID], *, include_deleted: bool = False) -> Sequence[T]:
        if not ids:
            return []
        stmt = self._select(include_deleted=include_deleted).where(self.model.id.in_(ids))
        return self.db.scalars(stmt).all()

    def exists_by_id(self, id: UUID, *, include_deleted: bool = False) -> bool:
        stmt = self._select(include_deleted=include_deleted).where(self.model.id == id)
        return bool(self.db.scalar(select(stmt.exists())))

    def save(self, entity: T) -> T:
        """Inserts or updates (flush only)."""
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def delete_by_id(self, id: UUID) -> bool:
        """Permanently deletes a record. Returns True if it existed."""
        entity = self.find_by_id(id, include_deleted=True)
        if entity is None:
            return False
        self.db.delete(entity)
        self.db.flush()
        return True


class SoftDeleteRepository[T: EntityBase](BaseRepository[T]):
    """Repository for entities with deleted_at: queries ignore deleted records by default."""

    def _select(self, *, include_deleted: bool = False) -> Select[tuple[T]]:
        stmt = select(self.model)
        return stmt if include_deleted else stmt.where(self.model.deleted_at.is_(None))

    def soft_delete_by_id(self, id: UUID, deleted_by: UUID | None = None) -> bool:
        """Marks an active record as deleted. Returns True if it existed."""
        entity = self.find_by_id(id)
        if entity is None:
            return False
        entity.deleted_at = datetime.now(UTC)
        entity.deleted_by = deleted_by
        self.db.flush()
        return True

    def restore_by_id(self, id: UUID, restored_by: UUID | None = None) -> T | None:
        """Restores a soft-deleted record, or returns None when not restorable."""
        entity = self.find_by_id(id, include_deleted=True)
        if entity is None or entity.deleted_at is None:
            return None
        entity.deleted_at = None
        entity.deleted_by = None
        if restored_by is not None:
            entity.updated_by = restored_by
        self.db.flush()
        self.db.refresh(entity)
        return entity
