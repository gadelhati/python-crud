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
from app.models.user import User


@pytest.fixture(scope="module", autouse=True)
def setup_test_database() -> Generator[None]:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> Generator[dict[str, str]]:
    """Cria um usuário inicial no banco para autenticar as requisições protegidas."""
    unique_suffix = uuid4().hex[:8]
    username = f"seed_admin_{unique_suffix}"
    password = "SeedAdminPassword123!"

    with SessionLocal() as db:
        from app.services.password import hash_password

        admin = User(
            username=username,
            email=f"seed.{unique_suffix}@example.com",
            password=hash_password(password),
            first_name="Seed",
            last_name="Admin",
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

    hard_delete_response = client.delete(f"/user/{user_id}/hard", headers=headers)
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

    headers = authentication_headers(client, payload["username"], payload["password"])
    hard_delete_response = client.delete(f"/user/{user['id']}/hard", headers=headers)
    assert hard_delete_response.status_code == 204


def test_user_soft_delete_restore_and_hard_delete(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    unique_suffix = uuid4().hex[:8]
    actor_payload = {
        "username": f"admin_{unique_suffix}",
        "email": f"admin.{unique_suffix}@example.com",
        "password": "AnotherPassword123!",
        "first_name": "Python",
        "last_name": "User",
    }
    payload = {
        "username": f"advanced_{unique_suffix}",
        "email": f"advanced.{unique_suffix}@example.com",
        "password": "AnotherPassword123!",
        "first_name": "Python",
        "last_name": "User",
    }

    actor_response = client.post("/user", json=actor_payload, headers=auth_headers)
    assert actor_response.status_code == 201, actor_response.json()
    actor_id = actor_response.json()["id"]

    create_response = client.post("/user", json=payload, headers=auth_headers)
    assert create_response.status_code == 201, create_response.json()
    user_id = create_response.json()["id"]

    headers = authentication_headers(
        client,
        actor_payload["username"],
        actor_payload["password"],
    )

    soft_delete_response = client.delete(f"/user/{user_id}", headers=headers)
    get_deleted_response = client.get(f"/user/{user_id}", headers=headers)
    restore_response = client.patch(f"/user/{user_id}/restore", headers=headers)
    hard_delete_response = client.delete(f"/user/{user_id}/hard", headers=headers)
    get_hard_deleted_response = client.get(f"/user/{user_id}", headers=headers)
    hard_delete_actor_response = client.delete(f"/user/{actor_id}/hard", headers=headers)

    assert soft_delete_response.status_code == 204, soft_delete_response.json()
    assert get_deleted_response.status_code == 404, get_deleted_response.json()
    assert restore_response.status_code == 200, restore_response.json()
    assert restore_response.json()["deleted_at"] is None, restore_response.json()
    assert hard_delete_response.status_code == 204, hard_delete_response.json()
    assert get_hard_deleted_response.status_code == 404, get_hard_deleted_response.json()
    assert hard_delete_actor_response.status_code == 204, hard_delete_actor_response.json()


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

    # Segunda tentativa deve ser bloqueada com 409 Conflict
    second_response = client.post("/admin/init/create-first-user", json=payload)
    assert second_response.status_code == 409
