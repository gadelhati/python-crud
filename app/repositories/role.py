from app.models.role import Role
from app.repositories.base import SoftDeleteRepository


class RoleRepository(SoftDeleteRepository[Role]):
    model = Role

    def find_defaults(self, *, include_deleted: bool = False) -> list[Role]:
        stmt = self._select(include_deleted=include_deleted).where(Role.is_default.is_(True))
        return list(self.db.scalars(stmt))
