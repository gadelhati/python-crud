from uuid import UUID

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app)


def test_application_initializes() -> None:
    with TestClient(app) as application_client:
        response = application_client.get("/openapi.json")

    assert response.status_code == 200

    openapi = response.json()

    assert openapi["openapi"].startswith("3.")
    assert isinstance(openapi["info"]["title"], str)
    assert openapi["info"]["title"].strip()
    assert "/" in openapi["paths"]
    assert "/health" in openapi["paths"]


def test_root_endpoint_returns_expected_response() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_health_endpoint_returns_expected_response() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_user_list_endpoint_initializes_database_schema() -> None:
    with TestClient(app) as application_client:
        response = application_client.get("/api/user")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_user_endpoints_use_uuid_identifiers() -> None:
    payload = {
        "username": "python_user",
        "email": "python.user@example.com",
        "password": "secure-password",
    }

    with TestClient(app) as application_client:
        create_response = application_client.post("/api/user", json=payload)

        assert create_response.status_code == 201
        user = create_response.json()
        user_id = UUID(user["id"])

        get_response = application_client.get(f"/api/user/{user_id}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == str(user_id)
    assert get_response.json()["deleted_at"] is None
    assert "password" not in get_response.json()
    assert "password_hash" not in get_response.json()

    with SessionLocal() as db:
        stored_user = db.get(User, user_id)
        assert stored_user is not None
        assert stored_user.password_hash != payload["password"]
        assert stored_user.password_hash.startswith("pbkdf2_sha256$")


def test_user_soft_delete_restore_and_hard_delete() -> None:
    payload = {
        "username": "advanced_user",
        "email": "advanced.user@example.com",
        "password": "another-secure-password",
    }

    with TestClient(app) as application_client:
        create_response = application_client.post("/api/user", json=payload)
        user_id = create_response.json()["id"]

        soft_delete_response = application_client.delete(f"/api/user/{user_id}")
        get_deleted_response = application_client.get(f"/api/user/{user_id}")
        restore_response = application_client.patch(f"/api/user/{user_id}/restore")
        hard_delete_response = application_client.delete(f"/api/user/{user_id}/hard")
        get_hard_deleted_response = application_client.get(f"/api/user/{user_id}")

    assert soft_delete_response.status_code == 204
    assert get_deleted_response.status_code == 404
    assert restore_response.status_code == 200
    assert restore_response.json()["deleted_at"] is None
    assert hard_delete_response.status_code == 204
    assert get_hard_deleted_response.status_code == 404
