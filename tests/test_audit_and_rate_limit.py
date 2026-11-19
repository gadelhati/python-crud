from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.config import settings
from app.database import SessionLocal
from app.models.role import Role
from app.models.user import User
from tests.conftest import authentication_headers, hash_password


def _create_regular_user(client: TestClient) -> tuple[UUID, dict[str, str]]:
    suffix = uuid4().hex[:8]
    username = f"regular_audit_{suffix}"
    password = "RegularUserPassword123!"

    with SessionLocal() as db:
        default_role = db.query(Role).filter(Role.name == "user").first()
        roles = [default_role] if default_role is not None else []
        user = User(
            username=username,
            email=f"regular.{suffix}@example.com",
            password=hash_password(password),
            first_name="Regular",
            last_name="User",
            roles=roles,
        )
        db.add(user)
        db.commit()
        user_id = user.id

    return user_id, authentication_headers(client, username, password)


def test_login_rate_limit_returns_429_when_exceeded(client: TestClient) -> None:
    max_requests = int(settings.rate_limit_login.split("/")[0])
    payload = {"username": "nonexistent_rate_limit_user", "password": "WrongPassword123!"}

    for _ in range(max_requests):
        response = client.post("/login", json=payload)
        assert response.status_code in (401, 429)

    blocked_response = client.post("/login", json=payload)
    assert blocked_response.status_code == 429


def test_refresh_and_bootstrap_rate_limits_return_429(client: TestClient) -> None:
    max_refresh = int(settings.rate_limit_refresh.split("/")[0])
    for _ in range(max_refresh):
        res = client.post("/login/refresh", json={"refresh_token": "invalid.token.value"})
        assert res.status_code in (401, 429)

    blocked_refresh = client.post("/login/refresh", json={"refresh_token": "invalid.token.value"})
    assert blocked_refresh.status_code == 429

    max_bootstrap = int(settings.rate_limit_bootstrap.split("/")[0])
    bootstrap_payload = {
        "username": "rate_limit_admin",
        "email": "ratelimit.admin@example.com",
        "password": "RateLimitPassword123!",
        "first_name": "Rate",
        "last_name": "Limit",
    }
    for _ in range(max_bootstrap):
        res = client.post("/admin/init/create-first-user", json=bootstrap_payload)
        assert res.status_code in (201, 409, 429)

    blocked_bootstrap = client.post("/admin/init/create-first-user", json=bootstrap_payload)
    assert blocked_bootstrap.status_code == 429

    try:
        for _ in range(max_bootstrap):
            res = client.post("/admin/init/create-first-user", json=bootstrap_payload)
            assert res.status_code in (201, 409, 429)

        blocked_bootstrap = client.post("/admin/init/create-first-user", json=bootstrap_payload)
        assert blocked_bootstrap.status_code == 429
    finally:
        with SessionLocal() as db:
            created = db.query(User).filter(User.username == bootstrap_payload["username"]).first()
            if created is not None:
                db.delete(created)
                db.commit()


def test_audit_endpoints_require_admin_role(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    regular_user_id, regular_headers = _create_regular_user(client)

    try:
        list_endpoints = ["/user/audit", "/role/audit", "/permission/audit"]
        for endpoint in list_endpoints:
            forbidden_res = client.get(endpoint, headers=regular_headers)
            assert forbidden_res.status_code == 403

            ok_res = client.get(endpoint, headers=auth_headers)
            assert ok_res.status_code == 200
            body = ok_res.json()
            assert isinstance(body["items"], list)
            assert body["total"] >= len(body["items"])
    finally:
        with SessionLocal() as db:
            stored_user = db.get(User, regular_user_id)
            if stored_user is not None:
                db.delete(stored_user)
                db.commit()


def test_user_and_role_audit_include_soft_deleted_records(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    suffix = uuid4().hex[:8]

    # 1. Cria e deleta (soft delete) um usuário para validar auditoria
    user_payload = {
        "username": f"audit_target_{suffix}",
        "email": f"audit.{suffix}@example.com",
        "password": "AuditTargetPassword123!",
        "first_name": "Audit",
        "last_name": "Target",
    }
    create_user_res = client.post("/user", json=user_payload, headers=auth_headers)
    assert create_user_res.status_code == 201, create_user_res.json()
    created_user_id = create_user_res.json()["id"]

    delete_user_res = client.delete(f"/user/{created_user_id}", headers=auth_headers)
    assert delete_user_res.status_code == 204

    user_audit_detail = client.get(f"/user/audit/{created_user_id}", headers=auth_headers)
    assert user_audit_detail.status_code == 200
    user_audit_data = user_audit_detail.json()
    assert user_audit_data["id"] == created_user_id
    assert user_audit_data["deleted_at"] is not None
    assert user_audit_data["deleted_by"] is not None
    assert user_audit_data["created_by"] is not None

    user_audit_list = client.get("/user/audit?limit=100", headers=auth_headers)
    assert user_audit_list.status_code == 200
    assert any(item["id"] == created_user_id for item in user_audit_list.json()["items"])

    # 2. Cria e deleta (soft delete) uma role para validar auditoria
    role_payload = {
        "name": f"audit_role_{suffix}",
        "description": "Role for audit verification",
        "is_default": False,
    }
    create_role_res = client.post("/role", json=role_payload, headers=auth_headers)
    assert create_role_res.status_code == 201, create_role_res.json()
    created_role_id = create_role_res.json()["id"]

    delete_role_res = client.delete(f"/role/{created_role_id}", headers=auth_headers)
    assert delete_role_res.status_code == 204

    role_audit_detail = client.get(f"/role/audit/{created_role_id}", headers=auth_headers)
    assert role_audit_detail.status_code == 200
    role_audit_data = role_audit_detail.json()
    assert role_audit_data["id"] == created_role_id
    assert role_audit_data["deleted_at"] is not None
    assert role_audit_data["deleted_by"] is not None

    # 3. Consulta listagem e detalhe de auditoria de permission
    perm_audit_list = client.get("/permission/audit", headers=auth_headers)
    assert perm_audit_list.status_code == 200
    permissions = perm_audit_list.json()["items"]
    assert len(permissions) > 0

    first_perm_id = permissions[0]["id"]
    perm_audit_detail = client.get(f"/permission/audit/{first_perm_id}", headers=auth_headers)
    assert perm_audit_detail.status_code == 200
    assert perm_audit_detail.json()["id"] == first_perm_id
    assert "created_at" in perm_audit_detail.json()

    # Limpeza física dos registros criados pelo teste
    client.delete(f"/user/{created_user_id}/hard", headers=auth_headers)
    client.delete(f"/role/{created_role_id}/hard", headers=auth_headers)
    with SessionLocal() as db:
        leftover_user = db.get(User, UUID(created_user_id))
        if leftover_user is not None:
            db.delete(leftover_user)
            db.commit()
