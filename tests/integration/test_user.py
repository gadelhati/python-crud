from uuid import UUID, uuid4

import pytest

from app.models.user import User

pytestmark = pytest.mark.integration


def _user_payload() -> dict:
    suffix = uuid4().hex
    return {
        "username": f"api_user_{suffix}",
        "email": f"api.user.{suffix}@example.com",
        "password": "SecurePassword123!",
        "first_name": "API",
        "last_name": "User",
    }


def test_user_creation_hashes_password_and_hides_it(client, auth_headers, db_session) -> None:
    payload = _user_payload()
    created = client.post("/user", json=payload, headers=auth_headers)
    assert created.status_code == 201, created.text
    user_id = UUID(created.json()["id"])

    try:
        assert "password" not in created.json()
        stored = db_session.get(User, user_id)
        assert stored is not None
        assert stored.password != payload["password"]
        assert stored.password.startswith("pbkdf2_sha256$")
    finally:
        client.delete(f"/user/{user_id}/hard", headers=auth_headers)


def test_user_soft_delete_restore_and_hard_delete(client, auth_headers) -> None:
    payload = _user_payload()
    created = client.post("/user", json=payload, headers=auth_headers)
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    soft_delete = client.delete(f"/user/{user_id}", headers=auth_headers)
    assert soft_delete.status_code == 204
    assert client.get(f"/user/{user_id}", headers=auth_headers).status_code == 404

    restored = client.patch(f"/user/{user_id}/restore", headers=auth_headers)
    assert restored.status_code == 200, restored.text
    assert restored.json()["id"] == user_id

    hard_delete = client.delete(f"/user/{user_id}/hard", headers=auth_headers)
    assert hard_delete.status_code == 204
    assert client.get(f"/user/{user_id}", headers=auth_headers).status_code == 404


def test_duplicate_username_and_email_return_conflict(client, auth_headers) -> None:
    payload = _user_payload()
    created = client.post("/user", json=payload, headers=auth_headers)
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    try:
        duplicate_username = client.post(
            "/user",
            json={**payload, "email": f"other.{uuid4().hex}@example.com"},
            headers=auth_headers,
        )
        assert duplicate_username.status_code == 409

        duplicate_email = client.post(
            "/user",
            json={**payload, "username": f"other_{uuid4().hex}"},
            headers=auth_headers,
        )
        assert duplicate_email.status_code == 409
    finally:
        client.delete(f"/user/{user_id}/hard", headers=auth_headers)


def test_admin_cannot_permanently_delete_own_account(client, auth_headers, db_session) -> None:
    from app.services.token import decode_access_token

    token = auth_headers["Authorization"].removeprefix("Bearer ")
    admin_id = decode_access_token(token)

    response = client.delete(f"/user/{admin_id}/hard", headers=auth_headers)
    assert response.status_code == 400
