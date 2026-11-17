from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm.exc import StaleDataError

from app.config import settings
from app.database import SessionLocal
from app.models.user import User
from app.services.base import ServiceError
from app.services.user import ServiceUser


def test_duplicate_username_and_email_return_409(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    suffix = uuid4().hex[:8]
    payload = {
        "username": f"unique_{suffix}",
        "email": f"unique.{suffix}@example.com",
        "password": "StrongPassword123!",
    }

    res1 = client.post("/user", json=payload, headers=auth_headers)
    assert res1.status_code == 201
    user_id = res1.json()["id"]

    # Mesmo username -> 409
    dup_user = client.post(
        "/user",
        json={**payload, "email": f"other.{suffix}@example.com"},
        headers=auth_headers,
    )
    assert dup_user.status_code == 409

    # Mesmo email -> 409
    dup_email = client.post(
        "/user",
        json={**payload, "username": f"other_{suffix}"},
        headers=auth_headers,
    )
    assert dup_email.status_code == 409

    # Restaurar um usuário que NÃO está deletado -> 400 Bad Request
    restore_active = client.patch(f"/user/{user_id}/restore", headers=auth_headers)
    assert restore_active.status_code == 400

    assert client.delete(f"/user/{user_id}/hard", headers=auth_headers).status_code == 204


def test_expired_and_malformed_tokens_return_401(client: TestClient) -> None:
    # 1. Token malformado
    bad_res = client.get("/user", headers={"Authorization": "Bearer token-invalido"})
    assert bad_res.status_code == 401

    # 2. Token expirado
    expired_payload = {
        "sub": str(uuid4()),
        "jti": str(uuid4()),
        "exp": datetime.now(UTC) - timedelta(minutes=5),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )
    exp_res = client.get("/user", headers={"Authorization": f"Bearer {expired_token}"})
    assert exp_res.status_code == 401


def test_optimistic_locking_raises_stale_data_error() -> None:
    """Valida que duas sessões simultâneas alterando o mesmo registro disparam StaleDataError."""
    suffix = uuid4().hex[:8]
    with SessionLocal() as db:
        u = User(
            username=f"concurrent_{suffix}",
            email=f"concurrent.{suffix}@example.com",
            password="hashed_password_placeholder",
        )
        db.add(u)
        db.commit()
        user_id = u.id

    with SessionLocal() as session_1, SessionLocal() as session_2:
        user_s1 = session_1.get(User, user_id)
        user_s2 = session_2.get(User, user_id)
        assert user_s1 is not None
        assert user_s2 is not None

        # Sessão 1 salva primeiro (version_id sobe de 1 para 2)
        user_s1.first_name = "SessionOne"
        session_1.commit()

        # Sessão 2 ainda tem version_id == 1 -> deve falhar no commit
        user_s2.first_name = "SessionTwo"
        with pytest.raises(StaleDataError):
            session_2.commit()
        session_2.rollback()

    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


def test_service_base_validation_helpers() -> None:
    """Cobre _validate_ids e _check_found diretamente no ServiceBase."""
    with SessionLocal() as db:
        service = ServiceUser(db)
        id1, id2 = uuid4(), uuid4()

        with pytest.raises(ServiceError, match="Cannot have more than"):
            service._validate_ids([id1, id2], max_items=1, label="roles")

        with pytest.raises(ServiceError, match="Duplicate"):
            service._validate_ids([id1, id1], max_items=5, label="roles")

        with pytest.raises(ServiceError, match="not found"):
            service._check_found([], [id1], label="roles")
