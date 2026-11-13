import os
from uuid import UUID, uuid4

os.environ.setdefault(
    "UVICORN_JWT_SECRET_KEY",
    "test-secret-key-with-at-least-thirty-two-characters",
)

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.user import User

client = TestClient(app)


def authentication_headers(
    application_client: TestClient,
    username: str,
    password: str,
) -> dict[str, str]:
    response = application_client.post(
        "/api/login",
        json={"username": username, "password": password},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


# def test_user_list_requires_authentication() -> None:
#     with TestClient(app) as application_client:
#         response = application_client.get("/api/user")

#     assert response.status_code == 401
#     assert response.headers["WWW-Authenticate"] == "Bearer"


def test_user_endpoints_use_uuid_identifiers() -> None:
    unique_suffix = uuid4().hex
    payload = {
        "username": f"python_user_{unique_suffix}",
        "email": f"python.user.{unique_suffix}@example.com",
        "password": "secure-password",
    }

    with TestClient(app) as application_client:
        create_response = application_client.post("/api/user", json=payload)

        assert create_response.status_code == 201
        user = create_response.json()
        user_id = UUID(user["id"])

        headers = authentication_headers(
            application_client,
            payload["username"],
            payload["password"],
        )
        get_response = application_client.get(f"/api/user/{user_id}", headers=headers)

        assert get_response.status_code == 200
        assert get_response.json()["id"] == str(user_id)
        assert get_response.json()["deleted_at"] is None
        assert "password" not in get_response.json()

        with SessionLocal() as db:
            stored_user = db.get(User, user_id)
            assert stored_user is not None
            assert stored_user.password != payload["password"]
            assert stored_user.password.startswith("pbkdf2_sha256$")

        hard_delete_response = application_client.delete(
            f"/api/user/{user_id}/hard",
            headers=headers,
        )

    assert hard_delete_response.status_code == 204


def test_user_soft_delete_restore_and_hard_delete() -> None:
    unique_suffix = uuid4().hex
    actor_payload = {
        "username": f"admin_user_{unique_suffix}",
        "email": f"admin.user.{unique_suffix}@example.com",
        "password": "another-secure-password",
    }
    payload = {
        "username": f"advanced_user_{unique_suffix}",
        "email": f"advanced.user.{unique_suffix}@example.com",
        "password": "another-secure-password",
    }

    with TestClient(app) as application_client:
        actor_response = application_client.post("/api/user", json=actor_payload)
        actor_id = actor_response.json()["id"]
        create_response = application_client.post("/api/user", json=payload)
        user_id = create_response.json()["id"]
        headers = authentication_headers(
            application_client,
            actor_payload["username"],
            actor_payload["password"],
        )

        soft_delete_response = application_client.delete(f"/api/user/{user_id}", headers=headers)
        get_deleted_response = application_client.get(f"/api/user/{user_id}", headers=headers)
        restore_response = application_client.patch(f"/api/user/{user_id}/restore", headers=headers)
        hard_delete_response = application_client.delete(
            f"/api/user/{user_id}/hard",
            headers=headers,
        )
        get_hard_deleted_response = application_client.get(f"/api/user/{user_id}", headers=headers)
        hard_delete_actor_response = application_client.delete(
            f"/api/user/{actor_id}/hard",
            headers=headers,
        )

    assert actor_response.status_code == 201
    assert soft_delete_response.status_code == 204
    assert get_deleted_response.status_code == 404
    assert restore_response.status_code == 200
    assert restore_response.json()["deleted_at"] is None
    assert hard_delete_response.status_code == 204
    assert get_hard_deleted_response.status_code == 404
    assert hard_delete_actor_response.status_code == 204
