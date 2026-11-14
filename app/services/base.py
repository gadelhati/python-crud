import logging
from collections.abc import Sequence
from math import ceil
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.base import EntityBase
from app.repositories.base import SoftDeleteRepository
from app.schemas.base import DTOPagination

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Generic error in the service layer."""

    def __init__(self, message: str, code: str = "service_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ServiceBase[
    M: EntityBase,
    C: BaseModel,
    U: BaseModel,
    R: BaseModel,
]:
    """Generic CRUD orchestration: rules, audit, transaction and DTO conversion.

    Queries live in the repository.
    """

    def __init__(
        self, db: Session, repository: SoftDeleteRepository[M], response_schema: type[R]
    ) -> None:
        self.db = db
        self.repository = repository
        self.response_schema = response_schema

    # ---- helpers ----------------------------------------------------------
    def _name(self) -> str:
        return self.repository.model.__name__

    def _to_dto(self, entity: M) -> R:
        return self.response_schema.model_validate(entity, from_attributes=True)

    def _get_or_404(self, id: UUID, *, include_deleted: bool = False) -> M:
        entity = self.repository.find_by_id(id, include_deleted=include_deleted)
        if entity is None:
            raise ServiceError(f"{self._name()} with id {id} not found", code="not_found")
        return entity

    @staticmethod
    def _stamp(entity: Any, user_id: UUID | None, *, created: bool = False) -> None:
        """Fills audit fields when the entity has them."""
        if created and hasattr(entity, "created_by"):
            entity.created_by = user_id
        if hasattr(entity, "updated_by"):
            entity.updated_by = user_id

    def _commit(self) -> None:
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error committing %s: %s", self._name(), e)
            if isinstance(e, IntegrityError):
                raise ServiceError(
                    f"Integrity error on {self._name()}", code="integrity_error"
                ) from e
            raise ServiceError(f"Unexpected error on {self._name()}") from e

    @staticmethod
    def _validate_ids(ids: Sequence[UUID], max_items: int, label: str) -> None:
        if len(ids) > max_items:
            raise ServiceError(
                f"Cannot have more than {max_items} {label}", code="validation_error"
            )
        if len(ids) != len(set(ids)):
            raise ServiceError(f"Duplicate {label} are not allowed", code="validation_error")

    @staticmethod
    def _check_found(found: Sequence[EntityBase], ids: Sequence[UUID], label: str) -> None:
        missing = set(ids) - {e.id for e in found}
        if missing:
            raise ServiceError(
                f"Some {label} not found: {', '.join(sorted(map(str, missing)))}",
                code=f"{label}_not_found",
            )

    # ---- CRUD -------------------------------------------------------------
    def get(self, id: UUID, include_deleted: bool = False) -> R:
        return self._to_dto(self._get_or_404(id, include_deleted=include_deleted))

    def list(self, page: int = 1, limit: int = 20, include_deleted: bool = False) -> dict[str, Any]:
        total = self.repository.count(include_deleted=include_deleted)
        items = self.repository.find_all(
            offset=(page - 1) * limit, limit=limit, include_deleted=include_deleted
        )
        total_pages = ceil(total / limit) if limit else 1
        return {
            "items": [self._to_dto(i) for i in items],
            "pagination": DTOPagination(
                total=total,
                page=page,
                limit=limit,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1,
            ),
        }

    def create(self, dto: C, current_user_id: UUID | None = None) -> R:
        entity = self.repository.model(**dto.model_dump(exclude_unset=True))
        self._stamp(entity, current_user_id, created=True)
        try:
            self.repository.save(entity)
        except SQLAlchemyError:
            self.db.rollback()
            raise ServiceError(f"Error creating {self._name()}", code="integrity_error") from None
        self._commit()
        return self._to_dto(entity)

    def update(self, id: UUID, dto: U, current_user_id: UUID | None = None) -> R:
        entity = self._get_or_404(id)
        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        self._stamp(entity, current_user_id)
        self._commit()
        return self._to_dto(entity)

    def delete(self, id: UUID) -> bool:
        """Hard delete."""
        if not self.repository.delete_by_id(id):
            raise ServiceError(f"{self._name()} with id {id} not found", code="not_found")
        self._commit()
        return True

    def soft_delete(self, id: UUID, current_user_id: UUID | None = None) -> bool:
        if not self.repository.soft_delete_by_id(id, current_user_id):
            raise ServiceError(f"{self._name()} with id {id} not found", code="not_found")
        self._commit()
        return True

    def restore(self, id: UUID, current_user_id: UUID | None = None) -> R:
        entity = self.repository.restore_by_id(id)
        if entity is None:
            raise ServiceError(
                f"{self._name()} with id {id} not found or not deleted", code="invalid_operation"
            )
        self._stamp(entity, current_user_id)
        self._commit()
        return self._to_dto(entity)
