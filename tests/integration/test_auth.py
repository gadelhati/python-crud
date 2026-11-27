from uuid import uuid4

import pytest

from app.models.user import User
from app.services.password import hash_password

pytestmark = pytest.mark.integration


def test_login_lockout_unlock_and_refresh_rotation(client, auth_headers, user_factory) -> None:
    target = user_factory(password="CorrectPassword123!")

    for _ in range(5):
        failed = client.post(
            "/login",
            json={"username": target.username, "password": "WrongPassword123!"},
        )
        assert failed.status_code == 401

    locked = client.post(
        "/login",
        json={"username": target.username, "password": "CorrectPassword123!"},
    )
    assert locked.status_code == 401

    # Administrative unlock is covered through the public endpoint.
    security = client.get(f"/user/{target.id}/security", headers=auth_headers)
    assert security.status_code == 200
    assert security.json()["is_locked"] is True
    assert security.json()["failed_attempts"] == 5

    unlock = client.patch(f"/user/{target.id}/unlock", headers=auth_headers)
    assert unlock.status_code == 204

    login = client.post(
        "/login",
        json={"username": target.username, "password": "CorrectPassword123!"},
    )
    assert login.status_code == 200
    old_refresh = login.json()["refresh_token"]

    rotated = client.post("/login/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    new_refresh = rotated.json()["refresh_token"]
    assert new_refresh != old_refresh

    replay = client.post("/login/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401

    logout = client.post(
        "/login/logout",
        json={"refresh_token": new_refresh},
        headers={"Authorization": f"Bearer {rotated.json()['access_token']}"},
    )
    assert logout.status_code == 204

    protected = client.get(
        f"/user/{target.id}/security",
        headers={"Authorization": f"Bearer {rotated.json()['access_token']}"},
    )
    assert protected.status_code == 401

    assert (
        client.post(
            "/login/refresh",
            json={"refresh_token": new_refresh},
        ).status_code
        == 401
    )


def test_login_rejects_inactive_user(client, db_session) -> None:
    user = User(
        username=f"inactive_{uuid4().hex}",
        email=f"inactive.{uuid4().hex}@example.com",
        password=hash_password("CorrectPassword123!"),
        is_active=False,
    )
    db_session.add(user)
    db_session.flush()

    response = client.post(
        "/login",
        json={"username": user.username, "password": "CorrectPassword123!"},
    )
    assert response.status_code == 401
