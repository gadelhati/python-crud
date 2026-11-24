# app/services/permission_policy.py - Permission delegation policy
from uuid import UUID

from app.enum.permission_action import EnumPermissionAction
from app.models.permission import Permission
from app.models.role import Role
from app.repositories.user import UserRepository
from app.services.base import ServiceError


class PermissionPolicy:
    """Enforces permission delegation rules."""

    @staticmethod
    def _get_actor_permissions(
        db,
        actor_id: UUID | None,
    ) -> set[EnumPermissionAction] | None:
        """Returns the actor's permissions, or None for administrators."""

        if actor_id is None:
            raise ServiceError(
                "Authenticated actor is required for permission delegation",
                code="forbidden",
            )

        actor = UserRepository(db).find_by_id(actor_id)

        if actor is None or not actor.is_active:
            raise ServiceError(
                "Actor not found or inactive",
                code="forbidden",
            )

        # Keep the same administrator rule used by dependencies.py.
        if any(role.name == "admin" for role in actor.roles):
            return None

        return {permission.action for role in actor.roles for permission in role.permissions}

    @classmethod
    def ensure_can_assign_roles(
        cls,
        db,
        actor_id: UUID | None,
        roles: list[Role],
    ) -> None:
        """Checks whether the actor can assign the requested roles."""

        actor_permissions = cls._get_actor_permissions(db, actor_id)

        if actor_permissions is None:
            return

        if any(role.is_system or role.name.casefold() == "admin" for role in roles):
            raise ServiceError(
                "System roles can only be assigned by administrators",
                code="forbidden",
            )

        delegated_permissions = {
            permission.action for role in roles for permission in role.permissions
        }

        if not delegated_permissions.issubset(actor_permissions):
            raise ServiceError(
                "Cannot assign roles containing permissions you do not possess",
                code="forbidden",
            )

    @classmethod
    def ensure_can_grant_permissions(
        cls,
        db,
        actor_id: UUID | None,
        permissions: list[Permission],
    ) -> None:
        """Checks whether the actor can grant the requested permissions."""

        actor_permissions = cls._get_actor_permissions(db, actor_id)

        if actor_permissions is None:
            return

        delegated_permissions = {permission.action for permission in permissions}

        if not delegated_permissions.issubset(actor_permissions):
            raise ServiceError(
                "Cannot grant permissions you do not possess",
                code="forbidden",
            )

    @classmethod
    def ensure_can_manage_role(
        cls,
        db,
        actor_id: UUID | None,
        role: Role,
    ) -> None:
        """Checks whether the actor can modify an existing role."""

        if role.is_system:
            raise ServiceError(
                "System roles cannot be modified",
                code="invalid_operation",
            )

        actor_permissions = cls._get_actor_permissions(db, actor_id)

        if actor_permissions is None:
            return

        existing_permissions = {permission.action for permission in role.permissions}

        if not existing_permissions.issubset(actor_permissions):
            raise ServiceError(
                "Cannot manage a role containing permissions you do not possess",
                code="forbidden",
            )

    @classmethod
    def ensure_can_change_default_status(
        cls,
        db,
        actor_id: UUID | None,
    ) -> None:
        """Ensures only administrators can change a role's default status."""

        actor_permissions = cls._get_actor_permissions(db, actor_id)

        if actor_permissions is not None:
            raise ServiceError(
                "Only administrators can change the default status of roles",
                code="forbidden",
            )
