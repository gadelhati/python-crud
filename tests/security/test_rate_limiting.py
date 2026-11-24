from uuid import uuid4

import pytest

from app.config import settings
from app.models.system_state import SystemState

pytestmark = pytest.mark.security


def test_login_rate_limit_returns_429(client) -> None:
    limit = int(settings.rate_limit_login.split("/")[0])
    payload = {
        "username": f"missing_{uuid4().hex}",
        "password": "InvalidPassword123!",
    }

    statuses = [client.post("/login", json=payload).status_code for _ in range(limit)]
    assert all(status in {401, 429} for status in statuses)
    assert client.post("/login", json=payload).status_code == 429


def test_refresh_rate_limit_returns_429(client) -> None:
    limit = int(settings.rate_limit_refresh.split("/")[0])

    for _ in range(limit):
        response = client.post(
            "/login/refresh",
            json={"refresh_token": "not.a.valid.token"},
        )
        assert response.status_code in {401, 429}

    assert (
        client.post(
            "/login/refresh",
            json={"refresh_token": "not.a.valid.token"},
        ).status_code
        == 429
    )


def test_bootstrap_rate_limit_returns_429(client, db_session) -> None:
    state = db_session.get(SystemState, 1)
    if state is None:
        db_session.add(SystemState(id=1, bootstrap_completed=False))
        db_session.flush()

    limit = int(settings.rate_limit_bootstrap.split("/")[0])
    payload = {
        "username": f"rate_admin_{uuid4().hex}",
        "email": f"rate.admin.{uuid4().hex}@example.com",
        "password": "RateLimitPassword123!",
        "first_name": "Rate",
        "last_name": "Limit",
    }

    for _ in range(limit):
        response = client.post("/admin/init/create-first-user", json=payload)
        assert response.status_code in {201, 409, 429}

    assert (
        client.post(
            "/admin/init/create-first-user",
            json=payload,
        ).status_code
        == 429
    )
