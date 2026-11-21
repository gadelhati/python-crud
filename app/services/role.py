# app/services/role.py - Service for handling role-related business logic
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.permission import PermissionRepository
from app.repositories.role import RoleRepository
from app.schemas.role import RoleRequest, RoleResponse
from app.services.base import ServiceBase, ServiceError
from app.services.permission_policy import PermissionPolicy
from app.validations.role import RoleValidation


class ServiceRole(ServiceBase[Role, RoleRequest, RoleRequest, RoleResponse]):
    """Role service with role-specific rules."""

    def __init__(self, db: Session) -> None:
        self.roles = RoleRepository(db)
        self.permissions = PermissionRepository(db)
        super().__init__(db, self.roles, RoleResponse)

    def _resolve_permissions(self, permission_ids: list[UUID]) -> list:
        self._validate_ids(permission_ids, RoleValidation.MAX_PERMISSIONS_PER_ROLE, "permissions")
        permissions = self.permissions.find_by_ids(permission_ids)
        self._check_found(permissions, permission_ids, "permissions")
        return list(permissions)

    def create(
        self,
        dto: RoleRequest,
        current_user_id: UUID | None = None,
    ) -> RoleResponse:
        if dto.name.casefold() == "admin":
            raise ServiceError(
                "The admin role name is reserved",
                code="invalid_operation",
            )

        if self.roles.find_by_name(dto.name, include_deleted=True) is not None:
            raise ServiceError(
                f"Role with name '{dto.name}' already exists",
                code="conflict",
            )

        permissions = self._resolve_permissions(dto.permission_ids) if dto.permission_ids else []

        PermissionPolicy.ensure_can_grant_permissions(
            self.db,
            current_user_id,
            permissions,
        )

        data = dto.model_dump(exclude_unset=True, exclude={"permission_ids"})
        role = Role(**data, permissions=permissions)

        self._stamp(role, current_user_id, created=True)
        self.roles.save(role)

        return self._to_dto(role)

    def update(
        self, id: UUID, dto: RoleRequest, current_user_id: UUID | None = None
    ) -> RoleResponse:
        role = self._get_or_404(id)

        PermissionPolicy.ensure_can_manage_role(
            self.db,
            current_user_id,
            role,
        )

        data = dto.model_dump(exclude_unset=True, exclude={"permission_ids"})

        if "name" in data and data["name"].casefold() == "admin":
            raise ServiceError(
                "The admin role name is reserved",
                code="invalid_operation",
            )

        if (
            "name" in data
            and data["name"] != role.name
            and self.roles.find_by_name(data["name"], include_deleted=True) is not None
        ):
            raise ServiceError(
                f"Role with name '{data['name']}' already exists",
                code="conflict",
            )

        if "permission_ids" in dto.model_fields_set:
            permissions = (
                self._resolve_permissions(dto.permission_ids) if dto.permission_ids else []
            )

            PermissionPolicy.ensure_can_grant_permissions(
                self.db,
                current_user_id,
                permissions,
            )

            role.permissions = permissions

        for field, value in data.items():
            setattr(role, field, value)

        self._stamp(role, current_user_id)
        self.roles.save(role)

        return self._to_dto(role)

    def delete(self, id: UUID) -> bool:
        role = self._get_or_404(id, include_deleted=True)
        if role.is_system:
            raise ServiceError("System roles cannot be deleted", code="invalid_operation")
        return super().delete(id)

    def soft_delete(self, id: UUID, current_user_id: UUID | None = None) -> bool:
        role = self._get_or_404(id)
        if role.is_system:
            raise ServiceError("System roles cannot be deleted", code="invalid_operation")
        return super().soft_delete(id, current_user_id)

    def get_default_roles(self, include_deleted: bool = False) -> list[RoleResponse]:
        return [self._to_dto(r) for r in self.roles.find_defaults(include_deleted=include_deleted)]

    def update_permissions(
        self,
        role_id: UUID,
        permission_ids: list[UUID],
        current_user_id: UUID | None = None,
    ) -> RoleResponse:
        role = self._get_or_404(role_id)

        PermissionPolicy.ensure_can_manage_role(
            self.db,
            current_user_id,
            role,
        )

        permissions = self._resolve_permissions(permission_ids)

        PermissionPolicy.ensure_can_grant_permissions(
            self.db,
            current_user_id,
            permissions,
        )

        role.permissions = permissions
        self._stamp(role, current_user_id)
        self.roles.save(role)

        return self._to_dto(role)
