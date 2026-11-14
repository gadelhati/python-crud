from uuid import UUID

from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.schemas.role import DTORoleCreate, DTORoleRetrieve, DTORoleUpdate
from app.services.base import ServiceBase
from app.validations.validation import Validation


class ServiceRole(ServiceBase[Role, DTORoleCreate, DTORoleUpdate, DTORoleRetrieve]):
    """Role service with role-specific rules."""

    def __init__(self, db: Session) -> None:
        self.roles = RoleRepository(db)
        self.permissions = PermissionRepository(db)
        super().__init__(db, self.roles, DTORoleRetrieve)

    def get_default_roles(self, include_deleted: bool = False) -> list[DTORoleRetrieve]:
        return [self._to_dto(r) for r in self.roles.find_defaults(include_deleted=include_deleted)]

    def update_permissions(
        self, role_id: UUID, permission_ids: list[UUID], current_user_id: UUID | None = None
    ) -> DTORoleRetrieve:
        self._validate_ids(permission_ids, Validation.MAX_PERMISSIONS_PER_ROLE, "permissions")
        role = self._get_or_404(role_id)
        permissions = self.permissions.find_by_ids(permission_ids)
        self._check_found(permissions, permission_ids, "permissions")

        role.permissions = list(permissions)
        self._stamp(role, current_user_id)
        self._commit()
        return self._to_dto(role)
