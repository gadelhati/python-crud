from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.config import settings
from app.services.base import ServiceError

_ALGORITHM = "HS256"


def _encode(user_id: UUID, secret: str, minutes: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires_at}, secret, algorithm=_ALGORITHM)


def _decode(token: str, secret: str) -> UUID:
    try:
        payload = jwt.decode(
            token, secret, algorithms=[_ALGORITHM], options={"require": ["exp", "sub"]}
        )
        return UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise ServiceError("Expired token", code="token_expired") from None
    except (jwt.InvalidTokenError, ValueError):
        raise ServiceError("Invalid token", code="invalid_token") from None


def create_access_token(user_id: UUID) -> str:
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
    return _decode(token, settings.jwt_secret_key.get_secret_value())


def decode_refresh_token(token: str) -> UUID:
    return _decode(token, settings.jwt_refresh_secret_key.get_secret_value())
