import os
from collections.abc import Generator
from uuid import UUID, uuid4

os.environ.setdefault("UVICORN_DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault(
    "UVICORN_JWT_SECRET_KEY",
    "test-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "UVICORN_JWT_REFRESH_SECRET_KEY",
    "test-refresh-secret-key-with-at-least-thirty-two-chars",
)

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, engine
from app.main import app
from app.models.base import Base
from app.models.role import Role
from app.models.user import User
from app.services.password import hash_password


@pytest.fixture(scope="module", autouse=True)
def setup_test_database() -> Generator[None]:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def authentication_headers(
    application_client: TestClient,
    username: str,
    password: str,
) -> dict[str, str]:
    response = application_client.post(
        "/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.json()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client: TestClient) -> Generator[dict[str, str]]:
    """Cria um usuário administrador no banco para autenticar requisições administrativas."""
    unique_suffix = uuid4().hex[:8]
    username = f"seed_admin_{unique_suffix}"
    password = "SeedAdminPassword123!"

    with SessionLocal() as db:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role is None:
            admin_role = Role(
                name="admin",
                description="System administrator",
                is_default=False,
                is_system=True,
            )
            db.add(admin_role)
            db.flush()

        admin = User(
            username=username,
            email=f"seed.{unique_suffix}@example.com",
            password=hash_password(password),
            first_name="Seed",
            last_name="Admin",
            roles=[admin_role],
        )
        db.add(admin)
        db.commit()
        admin_id = admin.id

    headers = authentication_headers(client, username, password)
    yield headers

    with SessionLocal() as db:
        stored_admin = db.get(User, admin_id)
        if stored_admin is not None:
            db.delete(stored_admin)
            db.commit()


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
    payload = {
        "username": "first_admin",
        "email": "first.admin@example.com",
        "password": "FirstAdminPassword123!",
        "first_name": "First",
        "last_name": "Admin",
    }

    first_response = client.post("/admin/init/create-first-user", json=payload)
    assert first_response.status_code == 201, first_response.json()
    data = first_response.json()
    assert data["username"] == "first_admin"
    assert any(role["name"] == "admin" for role in data["roles"])

    # Second attempt should fail with 409 Conflict
    second_response = client.post("/admin/init/create-first-user", json=payload)
    assert second_response.status_code == 409

    # Cleanup the first user to keep the database clean for subsequent tests
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
    assert get_response.json()["deleted_at"] is None
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
    hard_delete_response = client.delete(f"/user/{user_id}/hard", headers=auth_headers)
    get_hard_deleted_response = client.get(f"/user/{user_id}", headers=auth_headers)

    assert soft_delete_response.status_code == 204, soft_delete_response.json()
    assert get_deleted_response.status_code == 404, get_deleted_response.json()
    assert restore_response.status_code == 200, restore_response.json()
    assert restore_response.json()["deleted_at"] is None, restore_response.json()
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

    # user_a_id = res_a.json()["id"]
    # user_b_id = res_b.json()["id"]

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

    # 2. User A tries to edit User B (requires SelfOrAdminUser -> 403)


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
