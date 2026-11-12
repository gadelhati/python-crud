from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.config import settings

_ALGORITHM = "HS256"


def create_access_token(user_id: UUID) -> str:
    """Creates a time-limited JWT access token for a user."""
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        settings.jwt_secret_key.get_secret_value(),
        algorithm=_ALGORITHM,
    )


def decode_access_token(token: str) -> UUID:
    """Validates an access token and returns its user identifier."""
    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[_ALGORITHM],
    )
    return UUID(payload["sub"])
