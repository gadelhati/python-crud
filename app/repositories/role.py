# app/repository/base.py
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.repositories.base import SoftDeleteRepository


class RoleRepository(SoftDeleteRepository[Role]):
    model = Role

    def find_by_name(self, name: str, *, include_deleted: bool = False) -> Role | None:
        stmt = self._select(include_deleted=include_deleted).where(Role.name == name)
        return self.db.scalar(stmt)

    def find_by_id_with_permissions(
        self, id, *, include_deleted: bool = False
    ) -> Role | None:
        stmt = (
            self._select(include_deleted=include_deleted)
            .options(selectinload(Role.permissions))
            .where(Role.id == id)
        )
        return self.db.scalar(stmt)

    def find_defaults(self, *, include_deleted: bool = False) -> list[Role]:
        stmt = self._select(include_deleted=include_deleted).where(Role.is_default.is_(True))
        return list(self.db.scalars(stmt))
