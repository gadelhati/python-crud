from datetime import UTC, datetime

from app.dependencies import _has_permission, _is_admin
from app.enum.permission_action import EnumPermissionAction
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


def create_user(*roles: Role) -> User:
    return User(
        username="test_user",
        email="test@example.com",
        password="TestPassword123!",
        roles=list(roles),
    )


def create_role(
    name: str,
    *,
    permissions: list[Permission] | None = None,
    deleted: bool = False,
) -> Role:
    return Role(
        name=name,
        is_default=False,
        is_system=name == "admin",
        permissions=permissions or [],
        deleted_at=datetime.now(UTC) if deleted else None,
    )


def test_active_role_grants_permission() -> None:
    permission = Permission(
        name=EnumPermissionAction.CREATE_USER.value,
        action=EnumPermissionAction.CREATE_USER,
    )
    user = create_user(create_role("manager", permissions=[permission]))

    assert _has_permission(user, EnumPermissionAction.CREATE_USER)


def test_soft_deleted_role_does_not_grant_permission() -> None:
    permission = Permission(
        name=EnumPermissionAction.CREATE_USER.value,
        action=EnumPermissionAction.CREATE_USER,
    )
    user = create_user(create_role("manager", permissions=[permission], deleted=True))

    assert not _has_permission(user, EnumPermissionAction.CREATE_USER)


def test_soft_deleted_admin_role_does_not_grant_admin_access() -> None:
    user = create_user(create_role("admin", deleted=True))

    assert not _is_admin(user)
    assert not _has_permission(user, EnumPermissionAction.DELETE_ROLE)


def test_active_admin_role_retains_admin_access() -> None:
    user = create_user(create_role("admin"))

    assert _is_admin(user)
    assert _has_permission(user, EnumPermissionAction.DELETE_ROLE)


def test_restored_role_grants_permission_again() -> None:
    permission = Permission(
        name=EnumPermissionAction.CREATE_USER.value,
        action=EnumPermissionAction.CREATE_USER,
    )
    role = create_role("manager", permissions=[permission], deleted=True)
    user = create_user(role)

    assert not _has_permission(user, EnumPermissionAction.CREATE_USER)

    role.deleted_at = None

    assert _has_permission(user, EnumPermissionAction.CREATE_USER)
