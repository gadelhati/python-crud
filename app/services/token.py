# app/services/token.py - Service for handling JWT token creation and decoding
# for access and refresh tokens
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.config import settings
from app.services.base import ServiceError

_ALGORITHM = "HS256"


def _encode(user_id: UUID, secret: str, minutes: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=minutes)
    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "exp": expires_at,
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def _decode(token: str, secret: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[_ALGORITHM],
            options={"require": ["exp", "sub", "jti"]},
        )
        user_id = UUID(payload["sub"])
        jti = str(payload["jti"])
        expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
        return user_id, jti, expires_at
    except jwt.ExpiredSignatureError:
        raise ServiceError("Expired token", code="token_expired") from None
    except (jwt.InvalidTokenError, ValueError):
        raise ServiceError("Invalid token", code="invalid_token") from None


def create_access_token(user_id: UUID) -> str:
    assert settings.jwt_refresh_secret_key is not None
    return _encode(
        user_id,
        settings.jwt_secret_key.get_secret_value(),
        settings.jwt_access_token_expire_minutes,
    )


def create_refresh_token(user_id: UUID) -> str:
    return _encode(
        user_id,
        settings.jwt_refresh_secret_key.get_secret_value(),
        settings.jwt_refresh_token_expire_minutes,
    )


def decode_access_token(token: str) -> UUID:
    user_id, _, _ = _decode(token, settings.jwt_secret_key.get_secret_value())
    return user_id


def decode_refresh_token(token: str) -> tuple[UUID, str, datetime]:
    assert settings.jwt_refresh_secret_key is not None
    return _decode(token, settings.jwt_refresh_secret_key.get_secret_value())
