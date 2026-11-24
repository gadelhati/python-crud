from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.config import settings
from app.services.base import ServiceError
from app.services.token import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

pytestmark = pytest.mark.unit


def test_access_and_refresh_tokens_are_not_interchangeable() -> None:
    user_id = uuid4()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    assert decode_access_token(access_token) == user_id
    assert decode_refresh_token(refresh_token)[0] == user_id

    with pytest.raises(ServiceError) as access_error:
        decode_access_token(refresh_token)
    assert access_error.value.code == "invalid_token"

    with pytest.raises(ServiceError) as refresh_error:
        decode_refresh_token(access_token)
    assert refresh_error.value.code == "invalid_token"


def test_expired_access_token_is_rejected() -> None:
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

    with pytest.raises(ServiceError) as error:
        decode_access_token(token)
    assert error.value.code == "token_expired"


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c", "eyJhbGciOiJub25lIn0.e30."])
def test_malformed_access_tokens_are_rejected(token: str) -> None:
    with pytest.raises(ServiceError) as error:
        decode_access_token(token)
    assert error.value.code == "invalid_token"


def test_token_requires_all_security_claims() -> None:
    token = jwt.encode(
        {"sub": str(uuid4()), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret_key.get_secret_value(),
        algorithm="HS256",
    )

    with pytest.raises(ServiceError) as error:
        decode_access_token(token)
    assert error.value.code == "invalid_token"
