# app/services/token.py - JWT token creation and decoding
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.services.base import ServiceError

_ALGORITHM = "HS256"

TokenType = Literal["access", "refresh"]


def _encode(
    user_id: UUID,
    auth_version: int,
    secret: str,
    minutes: int,
    token_type: TokenType,
) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=minutes)

    payload = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "exp": expires_at,
        "token_type": token_type,
        "auth_version": auth_version,
    }

    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def _decode_with_version(
    token: str,
    secret: str,
    expected_type: TokenType,
) -> tuple[UUID, str, datetime, int]:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[_ALGORITHM],
            options={
                "require": ["exp", "sub", "jti", "token_type"],
            },
        )

        if payload["token_type"] != expected_type:
            raise jwt.InvalidTokenError("Invalid token type")

        user_id = UUID(payload["sub"])
        jti = str(payload["jti"])
        expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
        auth_version = payload.get("auth_version", 0)

        if not isinstance(auth_version, int) or auth_version < 0:
            raise jwt.InvalidTokenError("Invalid authentication version")

        return user_id, jti, expires_at, auth_version

    except jwt.ExpiredSignatureError:
        raise ServiceError("Expired token", code="token_expired") from None

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise ServiceError("Invalid token", code="invalid_token") from None


def _decode(
    token: str,
    secret: str,
    expected_type: TokenType,
) -> tuple[UUID, str, datetime]:
    user_id, jti, expires_at, _ = _decode_with_version(token, secret, expected_type)
    return user_id, jti, expires_at


def create_access_token(user_id: UUID, auth_version: int = 0) -> str:
    return _encode(
        user_id,
        auth_version,
        settings.jwt_secret_key.get_secret_value(),
        settings.jwt_access_token_expire_minutes,
        "access",
    )


def create_refresh_token(user_id: UUID, auth_version: int = 0) -> str:
    return _encode(
        user_id,
        auth_version,
        settings.jwt_refresh_secret_key.get_secret_value(),
        settings.jwt_refresh_token_expire_minutes,
        "refresh",
    )


def decode_access_token_claims(token: str) -> tuple[UUID, str, datetime]:
    """Decode an access token and return its identifying claims."""
    return _decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        "access",
    )


def decode_access_token_claims_with_version(
    token: str,
) -> tuple[UUID, str, datetime, int]:
    """Decode access token claims including authentication version."""
    return _decode_with_version(
        token,
        settings.jwt_secret_key.get_secret_value(),
        "access",
    )


def decode_access_token(token: str, db: Session | None = None) -> UUID:
    """Decode access token and optionally check whether it was revoked."""

    user_id, jti, _ = decode_access_token_claims(token)

    if db is not None:
        from app.models.revoked_token import RevokedToken

        stmt = select(RevokedToken.jti).where(RevokedToken.jti == jti)

        if db.scalar(stmt) is not None:
            raise ServiceError("Token has been revoked", code="invalid_token")

    return user_id


def decode_refresh_token(token: str) -> tuple[UUID, str, datetime]:
    return _decode(
        token,
        settings.jwt_refresh_secret_key.get_secret_value(),
        "refresh",
    )


def decode_refresh_token_claims_with_version(
    token: str,
) -> tuple[UUID, str, datetime, int]:
    """Decode refresh token claims including authentication version."""
    return _decode_with_version(
        token,
        settings.jwt_refresh_secret_key.get_secret_value(),
        "refresh",
    )
