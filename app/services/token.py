# app/services/token.py - Service for handling JWT token creation and decoding
# for access and refresh tokens
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
    }

    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def _decode(
    token: str,
    secret: str,
    expected_type: TokenType,
) -> tuple[UUID, str, datetime]:
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

        return user_id, jti, expires_at

    except jwt.ExpiredSignatureError:
        raise ServiceError("Expired token", code="token_expired") from None

    except (jwt.InvalidTokenError, ValueError):
        raise ServiceError("Invalid token", code="invalid_token") from None


def create_access_token(user_id: UUID) -> str:
    return _encode(
        user_id,
        settings.jwt_secret_key.get_secret_value(),
        settings.jwt_access_token_expire_minutes,
        "access",
    )


def create_refresh_token(user_id: UUID) -> str:
    return _encode(
        user_id,
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


def decode_access_token(token: str, db: Session | None = None) -> UUID:
    """Decode access token and optionally check if revoked."""

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
