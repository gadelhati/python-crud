from uuid import uuid4

import pytest

from app.enum.permission_action import EnumPermissionAction
from app.models.role import Role
from app.models.user import User
from app.services.password import hash_password
from tests.conftest import authentication_headers

pytestmark = pytest.mark.security


def _actor_with_permissions(db_session, permission_factory, actions):
    role = Role(
        name=f"delegator_{uuid4().hex}",
        description="Limited delegator",
        permissions=[permission_factory(action) for action in actions],
    )
    db_session.add(role)
    db_session.flush()

    user = User(
        username=f"delegator_{uuid4().hex}",
        email=f"delegator.{uuid4().hex}@example.com",
        password=hash_password("DelegatorPassword123!"),
        roles=[role],
    )
    db_session.add(user)
    db_session.flush()
    return user


def test_non_admin_cannot_create_default_role(
    client,
    db_session,
    permission_factory,
):
    actor = _actor_with_permissions(
        db_session,
        permission_factory,
        [EnumPermissionAction.CREATE_ROLE],
    )
    headers = authentication_headers(client, actor.username, "DelegatorPassword123!")

    response = client.post(
        "/role",
        json={
            "name": f"forbidden_default_{uuid4().hex}",
            "description": "Must not become default",
            "is_default": True,
            "permission_ids": [],
        },
        headers=headers,
    )
    assert response.status_code == 403


def test_non_admin_cannot_grant_permission_the_actor_does_not_have(
    client,
    db_session,
    permission_factory,
):
    actor = _actor_with_permissions(
        db_session,
        permission_factory,
        [EnumPermissionAction.CREATE_ROLE],
    )
    forbidden_permission = permission_factory(EnumPermissionAction.UPDATE_USER)
    headers = authentication_headers(client, actor.username, "DelegatorPassword123!")

    response = client.post(
        "/role",
        json={
            "name": f"privileged_role_{uuid4().hex}",
            "description": "Privilege escalation attempt",
            "is_default": False,
            "permission_ids": [str(forbidden_permission.id)],
        },
        headers=headers,
    )
    assert response.status_code == 403


def test_non_admin_cannot_assign_system_admin_role(
    client,
    db_session,
    permission_factory,
):
    actor = _actor_with_permissions(
        db_session,
        permission_factory,
        [EnumPermissionAction.CREATE_USER],
    )
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    if admin_role is None:
        admin_role = Role(
            name="admin",
            description="System administrator",
            is_default=False,
            is_system=True,
        )
        db_session.add(admin_role)
        db_session.flush()

    headers = authentication_headers(client, actor.username, "DelegatorPassword123!")
    suffix = uuid4().hex
    response = client.post(
        "/user",
        json={
            "username": f"escalation_{suffix}",
            "email": f"escalation.{suffix}@example.com",
            "password": "TargetPassword123!",
            "role_ids": [str(admin_role.id)],
        },
        headers=headers,
    )
    assert response.status_code == 403


def test_non_admin_cannot_manage_role_with_unowned_permissions(
    client,
    db_session,
    permission_factory,
):
    actor = _actor_with_permissions(
        db_session,
        permission_factory,
        [
            EnumPermissionAction.UPDATE_ROLE,
            EnumPermissionAction.CREATE_ROLE,
        ],
    )
    sensitive_permission = permission_factory(EnumPermissionAction.UPDATE_USER)
    target_role = Role(
        name=f"sensitive_{uuid4().hex}",
        description="Role with a permission the actor does not possess",
        permissions=[sensitive_permission],
    )
    db_session.add(target_role)
    db_session.flush()

    headers = authentication_headers(client, actor.username, "DelegatorPassword123!")
    response = client.put(
        f"/role/{target_role.id}",
        json={
            "name": target_role.name,
            "description": "Attempted modification",
            "is_default": False,
            "permission_ids": [],
        },
        headers=headers,
    )
    assert response.status_code == 403
