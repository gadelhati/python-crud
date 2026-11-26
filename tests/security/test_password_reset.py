"""Tests for password reset workflow."""

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models.password_reset_token import PasswordResetToken
from app.services.base import ServiceError
from app.services.password import hash_password, verify_password
from app.services.password_reset import ServicePasswordReset


def test_password_reset_request_returns_generic_response(
    client: TestClient,
    user_factory,
    monkeypatch,
) -> None:
    """Registered and unregistered emails must receive the same response."""

    user = user_factory()

    monkeypatch.setattr(
        "app.services.password_reset.send_password_reset_email",
        lambda recipient, reset_url: None,
    )
    monkeypatch.setattr(
        settings,
        "password_reset_url",
        "https://frontend.example.com/reset-password",
    )

    registered = client.post(
        "/login/password-reset/request",
        json={"email": user.email},
    )
    unregistered = client.post(
        "/login/password-reset/request",
        json={"email": "unknown@example.com"},
    )

    assert registered.status_code == 202
    assert unregistered.status_code == 202
    assert registered.json() == unregistered.json()


def test_password_reset_changes_password_and_invalidates_old_tokens(
    client: TestClient,
    db_session: Session,
    user_factory,
    monkeypatch,
) -> None:
    """A successful reset changes the password and invalidates old sessions."""

    user = user_factory()
    old_password = "UserPassword123!"
    new_password = "NewPassword456!"

    user.password = hash_password(old_password)
    db_session.flush()

    monkeypatch.setattr(
        settings,
        "password_reset_url",
        "https://frontend.example.com/reset-password",
    )

    captured: dict[str, str] = {}

    def fake_send_email(recipient: str, reset_url: str) -> None:
        captured["recipient"] = recipient
        captured["url"] = reset_url

    monkeypatch.setattr(
        "app.services.password_reset.send_password_reset_email",
        fake_send_email,
    )

    login_response = client.post(
        "/login",
        json={
            "username": user.username,
            "password": old_password,
        },
    )

    assert login_response.status_code == 200

    old_access_token = login_response.json()["access_token"]
    old_refresh_token = login_response.json()["refresh_token"]

    request_response = client.post(
        "/login/password-reset/request",
        json={"email": user.email},
    )

    assert request_response.status_code == 202
    assert captured["recipient"] == user.email

    query = parse_qs(urlsplit(captured["url"]).query)
    reset_token = query["token"][0]

    confirm_response = client.post(
        "/login/password-reset/confirm",
        json={
            "token": reset_token,
            "new_password": new_password,
        },
    )

    assert confirm_response.status_code == 204

    db_session.refresh(user)

    assert verify_password(new_password, user.password)
    assert user.auth_version == 1

    refresh_response = client.post(
        "/login/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert refresh_response.status_code == 401

    access_response = client.get(
        "/user",
        headers={"Authorization": f"Bearer {old_access_token}"},
    )

    assert access_response.status_code == 401


def test_password_reset_token_can_only_be_used_once(
    client: TestClient,
    user_factory,
    monkeypatch,
) -> None:
    """A consumed reset token must be rejected."""

    user = user_factory()

    monkeypatch.setattr(
        settings,
        "password_reset_url",
        "https://frontend.example.com/reset-password",
    )

    captured: dict[str, str] = {}

    def fake_send_email(recipient: str, reset_url: str) -> None:
        captured["url"] = reset_url

    monkeypatch.setattr(
        "app.services.password_reset.send_password_reset_email",
        fake_send_email,
    )

    request_response = client.post(
        "/login/password-reset/request",
        json={"email": user.email},
    )

    assert request_response.status_code == 202

    reset_token = parse_qs(urlsplit(captured["url"]).query)["token"][0]

    first_response = client.post(
        "/login/password-reset/confirm",
        json={
            "token": reset_token,
            "new_password": "NewPassword456!",
        },
    )

    second_response = client.post(
        "/login/password-reset/confirm",
        json={
            "token": reset_token,
            "new_password": "AnotherPassword789!",
        },
    )

    assert first_response.status_code == 204
    assert second_response.status_code == 401


def test_password_reset_invalid_token_is_rejected(client: TestClient) -> None:
    """An unknown token must be rejected."""

    response = client.post(
        "/login/password-reset/confirm",
        json={
            "token": "invalid-token",
            "new_password": "NewPassword456!",
        },
    )

    assert response.status_code == 401


def test_password_reset_email_failure_does_not_reveal_account(
    client: TestClient,
    user_factory,
    monkeypatch,
) -> None:
    """SMTP errors must not disclose whether the account exists."""

    user = user_factory()

    monkeypatch.setattr(
        settings,
        "password_reset_url",
        "https://frontend.example.com/reset-password",
    )

    def fail_sending_email(recipient: str, reset_url: str) -> None:
        raise RuntimeError("SMTP unavailable")

    monkeypatch.setattr(
        "app.services.password_reset.send_password_reset_email",
        fail_sending_email,
    )

    response = client.post(
        "/login/password-reset/request",
        json={"email": user.email},
    )

    assert response.status_code == 202
    assert "registered" in response.json()["message"].lower()


def test_build_reset_url_requires_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "password_reset_url", None)

    with pytest.raises(
        RuntimeError,
        match="Password reset URL is not configured",
    ):
        ServicePasswordReset._build_reset_url("test-token")


def test_password_reset_rejects_inactive_user(
    db_session: Session,
    user_factory,
) -> None:
    user = user_factory()
    user.is_active = False

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=ServicePasswordReset._hash_token("valid-token"),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    db_session.add(reset_token)
    db_session.flush()

    service = ServicePasswordReset(db_session)

    with pytest.raises(ServiceError) as error:
        service.confirm_reset("valid-token", "NewPassword456!")

    assert error.value.code == "invalid_token"
