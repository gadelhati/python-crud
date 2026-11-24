from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.config import settings

pytestmark = pytest.mark.security


def test_missing_or_malformed_bearer_token_is_rejected(client) -> None:
    assert client.get("/user").status_code == 401
    response = client.get("/user", headers={"Authorization": "Bearer malformed"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_expired_access_token_is_rejected_by_api(client) -> None:
    payload = {
        "sub": str(uuid4()),
        "jti": str(uuid4()),
        "exp": datetime.now(UTC) - timedelta(minutes=1),
        "token_type": "access",
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )
    response = client.get("/user", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_access_token_is_rejected_after_user_deactivation(
    client,
    auth_headers,
    user_factory,
):
    from tests.conftest import authentication_headers

    target = user_factory(password="ActivePassword123!")
    user_headers = authentication_headers(client, target.username, "ActivePassword123!")

    assert client.get(f"/user/{target.id}", headers=user_headers).status_code == 200

    update = client.put(
        f"/user/{target.id}",
        json={
            "username": target.username,
            "email": target.email,
            "first_name": "Test",
            "last_name": "User",
            "is_active": False,
        },
        headers=auth_headers,
    )
    assert update.status_code == 200
    assert update.json()["is_active"] is False

    rejected = client.get(f"/user/{target.id}", headers=user_headers)
    assert rejected.status_code == 401
    assert rejected.headers["WWW-Authenticate"] == "Bearer"
