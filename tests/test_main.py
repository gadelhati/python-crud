import os
from uuid import UUID, uuid4

from app.models.system_state import SystemState

os.environ.setdefault("UVICORN_DATABASE_URL", "sqlite:///./db_test.sqlite3")
os.environ.setdefault(
    "UVICORN_JWT_SECRET_KEY",
    "test-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "UVICORN_JWT_REFRESH_SECRET_KEY",
    "test-refresh-secret-key-with-at-least-thirty-two-chars",
)

from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.database import SessionLocal
from app.models.user import User
from tests.conftest import authentication_headers


def assert_test_database(database_url: str) -> None:
    url = make_url(database_url)

    if url.get_backend_name() == "sqlite":
        return

    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Unsupported test database")

    if url.database != "python_crud_test":
        raise RuntimeError("Tests can only run against the dedicated test database")


def test_application_initializes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi = response.json()
    assert openapi["openapi"].startswith("3.")
    assert isinstance(openapi["info"]["title"], str)
    assert openapi["info"]["title"].strip()
    assert "/" in openapi["paths"]
    assert "/health" in openapi["paths"]


def test_root_endpoint_returns_expected_response(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_health_endpoint_returns_expected_response(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_first_user_endpoint(client: TestClient) -> None:

    # 1. Initialize the bootstrap state in the test database.
    with SessionLocal() as db:
        db.add(
            SystemState(
                id=1,
                bootstrap_completed=False,
            )
        )
        db.commit()

    # 2. Prepare the request payload.
    payload = {
        "username": "first_admin",
        "email": "first.admin@example.com",
        "password": "FirstAdminPassword123!",
        "first_name": "First",
        "last_name": "Admin",
    }

    # 3. First request must create the administrator.
    first_response = client.post(
        "/admin/init/create-first-user",
        json=payload,
    )
    assert first_response.status_code == 201, first_response.json()

    data = first_response.json()
    assert data["username"] == "first_admin"
    assert any(role["name"] == "admin" for role in data["roles"])

    # 4. Second request must return 409 Conflict.
    second_response = client.post(
        "/admin/init/create-first-user",
        json=payload,
    )
    assert second_response.status_code == 409

    # 5. Verify that bootstrap remains completed.
    with SessionLocal() as db:
        state = db.get(SystemState, 1)
        assert state is not None
        assert state.bootstrap_completed is True

    # 6. Cleanup the first user.
    with SessionLocal() as db:
        created_user = db.get(User, UUID(data["id"]))
        if created_user is not None:
            db.delete(created_user)
            db.commit()


def test_user_list_requires_authentication(client: TestClient) -> None:
    response = client.get("/user")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_user_endpoints_use_uuid_identifiers(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    unique_suffix = uuid4().hex[:8]
    payload = {
        "username": f"python_user_{unique_suffix}",
        "email": f"python.user.{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "first_name": "Python",
        "last_name": "User",
    }

    create_response = client.post("/user", json=payload, headers=auth_headers)
    assert create_response.status_code == 201, create_response.json()
    user = create_response.json()
    user_id = UUID(user["id"])

    headers = authentication_headers(client, payload["username"], payload["password"])
    get_response = client.get(f"/user/{user_id}", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["id"] == str(user_id)
    assert get_response.json()["first_name"] == payload["first_name"]
    assert get_response.json()["last_name"] == payload["last_name"]
    assert "password" not in get_response.json()

    with SessionLocal() as db:
        stored_user = db.get(User, user_id)
        assert stored_user is not None
        assert stored_user.password != payload["password"]
        assert stored_user.password.startswith("pbkdf2_sha256$")

    hard_delete_response = client.delete(f"/user/{user_id}/hard", headers=auth_headers)
    assert hard_delete_response.status_code == 204


def test_user_names_can_be_null(client: TestClient, auth_headers: dict[str, str]) -> None:
    unique_suffix = uuid4().hex[:8]
    payload = {
        "username": f"nameless_{unique_suffix}",
        "email": f"nameless.{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "first_name": None,
        "last_name": None,
    }

    create_response = client.post("/user", json=payload, headers=auth_headers)
    assert create_response.status_code == 201, create_response.json()
    user = create_response.json()
    assert user["first_name"] is None
    assert user["last_name"] is None

    hard_delete_response = client.delete(f"/user/{user['id']}/hard", headers=auth_headers)
    assert hard_delete_response.status_code == 204


def test_user_soft_delete_restore_and_hard_delete(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    unique_suffix = uuid4().hex[:8]
    target_payload = {
        "username": f"advanced_{unique_suffix}",
        "email": f"advanced.{unique_suffix}@example.com",
        "password": "AnotherPassword123!",
        "first_name": "Python",
        "last_name": "User",
    }

    create_response = client.post("/user", json=target_payload, headers=auth_headers)
    assert create_response.status_code == 201, create_response.json()
    user_id = create_response.json()["id"]

    soft_delete_response = client.delete(f"/user/{user_id}", headers=auth_headers)
    get_deleted_response = client.get(f"/user/{user_id}", headers=auth_headers)
    restore_response = client.patch(f"/user/{user_id}/restore", headers=auth_headers)

    assert soft_delete_response.status_code == 204, soft_delete_response.json()
    assert get_deleted_response.status_code == 404, get_deleted_response.json()
    assert restore_response.status_code == 200, restore_response.json()
    with SessionLocal() as db:
        restored_user = db.get(User, UUID(user_id))
        assert restored_user is not None
        assert restored_user.deleted_at is None

    hard_delete_response = client.delete(f"/user/{user_id}/hard", headers=auth_headers)
    get_hard_deleted_response = client.get(f"/user/{user_id}", headers=auth_headers)
    assert hard_delete_response.status_code == 204, hard_delete_response.json()
    assert get_hard_deleted_response.status_code == 404, get_hard_deleted_response.json()


def test_regular_user_cannot_modify_or_delete_other_users(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Ensures that a regular user receives 403 Forbidden when trying
    to modify/delete other users."""
    suffix = uuid4().hex[:8]

    user_a_payload = {
        "username": f"user_a_{suffix}",
        "email": f"user.a.{suffix}@example.com",
        "password": "RegularPassword123!",
        "first_name": "User",
        "last_name": "Alpha",
    }
    user_b_payload = {
        "username": f"user_b_{suffix}",
        "email": f"user.b.{suffix}@example.com",
        "password": "RegularPassword123!",
        "first_name": "User",
        "last_name": "Beta",
    }

    res_a = client.post("/user", json=user_a_payload, headers=auth_headers)
    res_b = client.post("/user", json=user_b_payload, headers=auth_headers)
    assert res_a.status_code == 201
    assert res_b.status_code == 201

    user_a_id = res_a.json()["id"]
    user_b_id = res_b.json()["id"]

    headers_a = authentication_headers(
        client, user_a_payload["username"], user_a_payload["password"]
    )

    # 1. User A tries to create another user (requires AdminUser -> 403)
    create_forbidden = client.post(
        "/user",
        json={
            "username": f"intruder_{suffix}",
            "email": f"intruder.{suffix}@example.com",
            "password": "RegularPassword123!",
        },
        headers=headers_a,
    )
    assert create_forbidden.status_code == 403

    # Cleanup
    assert (
        client.delete(
            f"/user/{user_a_id}/hard",
            headers=auth_headers,
        ).status_code
        == 204
    )

    assert (
        client.delete(
            f"/user/{user_b_id}/hard",
            headers=auth_headers,
        ).status_code
        == 204
    )


def test_login_lockout_unlock_and_refresh_token(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    suffix = uuid4().hex[:8]
    payload = {
        "username": f"lock_user_{suffix}",
        "email": f"lock.{suffix}@example.com",
        "password": "CorrectPassword123!",
        "first_name": "Lock",
        "last_name": "Test",
    }

    create_res = client.post("/user", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    user_id = create_res.json()["id"]

    # 1. Executa 5 tentativas falhas consecutivas (401 Unauthorized)
    for _ in range(5):
        fail_res = client.post(
            "/login",
            json={"username": payload["username"], "password": "WrongPassword!"},
        )
        assert fail_res.status_code == 401

    # 2. Na 6ª tentativa, mesmo com a senha correta, a conta deve estar bloqueada (423 Locked)
    locked_res = client.post(
        "/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert locked_res.status_code == 423

    # 3. Administrador verifica o status de segurança e desbloqueia a conta
    sec_res = client.get(f"/user/{user_id}/security", headers=auth_headers)
    assert sec_res.status_code == 200
    assert sec_res.json()["is_locked"] is True
    assert sec_res.json()["failed_attempts"] == 5

    unlock_res = client.patch(f"/user/{user_id}/unlock", headers=auth_headers)
    assert unlock_res.status_code == 204

    # 4. Login volta a funcionar e retorna access_token + refresh_token
    login_res = client.post(
        "/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert tokens["refresh_token"] is not None

    # 5. Rotação de sessão via /login/refresh
    refresh_res = client.post(
        "/login/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    # Limpeza
    assert client.delete(f"/user/{user_id}/hard", headers=auth_headers).status_code == 204


def test_login_lockout_unlock_and_refresh_token_blacklist(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Testa bloqueio por 5 tentativas falhas, desbloqueio, rotação e blacklist de refresh token."""
    suffix = uuid4().hex[:8]
    payload = {
        "username": f"lock_user_{suffix}",
        "email": f"lock.{suffix}@example.com",
        "password": "CorrectPassword123!",
        "first_name": "Lock",
        "last_name": "Test",
    }

    # Cria um usuário de teste usando o token de administrador (auth_headers)
    create_res = client.post("/user", json=payload, headers=auth_headers)
    assert create_res.status_code == 201, create_res.json()
    user_id = create_res.json()["id"]

    # 1. Simula 5 tentativas de login com senha errada -> deve retornar 401 em todas
    for _ in range(5):
        fail_res = client.post(
            "/login",
            json={"username": payload["username"], "password": "WrongPassword!"},
        )
        assert fail_res.status_code == 401

    # 2. Na 6ª tentativa, mesmo acertando a senha, a conta deve estar bloqueada -> 423 Locked
    locked_res = client.post(
        "/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert locked_res.status_code == 423

    # 3. Administrador consulta o status de segurança e desbloqueia a conta
    sec_res = client.get(f"/user/{user_id}/security", headers=auth_headers)
    assert sec_res.status_code == 200
    assert sec_res.json()["is_locked"] is True
    assert sec_res.json()["failed_attempts"] == 5

    unlock_res = client.patch(f"/user/{user_id}/unlock", headers=auth_headers)
    assert unlock_res.status_code == 204

    # 4. Após desbloqueio, o login volta a funcionar e devolve access_token + refresh_token
    login_res = client.post(
        "/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    old_refresh = tokens["refresh_token"]
    assert old_refresh is not None

    # 5. Rotação de sessão: usa o old_refresh para obter um novo par de tokens -> 200 OK
    first_refresh = client.post("/login/refresh", json={"refresh_token": old_refresh})
    assert first_refresh.status_code == 200
    new_refresh = first_refresh.json()["refresh_token"]
    assert new_refresh != old_refresh

    # 6. Blacklist: tentar reutilizar o old_refresh já usado deve ser bloqueado -> 401 Unauthorized
    replay_res = client.post("/login/refresh", json={"refresh_token": old_refresh})
    assert replay_res.status_code == 401

    # 7. Logout: invalida também o new_refresh e impede uso futuro -> 204 depois 401
    logout_res = client.post("/login/logout", json={"refresh_token": new_refresh})
    assert logout_res.status_code == 204

    after_logout_res = client.post("/login/refresh", json={"refresh_token": new_refresh})
    assert after_logout_res.status_code == 401

    # Limpeza do usuário de teste
    assert client.delete(f"/user/{user_id}/hard", headers=auth_headers).status_code == 204


def test_admin_can_update_other_user_and_record_audit_trail(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    """Garante que o admin atualize terceiros e preencha updated_by com seu próprio UUID."""
    suffix = uuid4().hex[:8]
    target_payload = {
        "username": f"target_user_{suffix}",
        "email": f"target.{suffix}@example.com",
        "password": "TargetPassword123!",
        "first_name": "Before",
        "last_name": "Update",
    }

    create_res = client.post("/user", json=target_payload, headers=auth_headers)
    assert create_res.status_code == 201, create_res.json()
    target_data = create_res.json()
    target_id = target_data["id"]

    with SessionLocal() as db:
        created_user = db.get(User, UUID(target_id))
        assert created_user is not None
        admin_id = str(created_user.created_by)
        assert created_user.created_by is not None

    update_payload = {
        "username": target_payload["username"],
        "email": target_payload["email"],
        "first_name": "After",
        "last_name": "AdminEdit",
    }
    update_res = client.put(f"/user/{target_id}", json=update_payload, headers=auth_headers)
    assert update_res.status_code == 200, update_res.json()

    updated_data = update_res.json()
    assert updated_data["first_name"] == "After"
    assert updated_data["last_name"] == "AdminEdit"

    # Confirma diretamente no banco de dados
    with SessionLocal() as db:
        stored_user = db.get(User, UUID(target_id))
        assert stored_user is not None
        assert str(stored_user.updated_by) == admin_id
        assert stored_user.version_id == 2

    # Limpeza
    assert client.delete(f"/user/{target_id}/hard", headers=auth_headers).status_code == 204
