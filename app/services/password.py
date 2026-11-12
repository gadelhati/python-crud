import base64
import hashlib
import secrets

_ITERATIONS = 600_000
_SALT_SIZE = 16


def hash_password(password: str) -> str:
    """Returns a PBKDF2-HMAC-SHA256 hash suitable for database storage."""
    salt = secrets.token_bytes(_SALT_SIZE)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _ITERATIONS,
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_hash = base64.urlsafe_b64encode(password_hash).decode("ascii")
    return f"pbkdf2_sha256${_ITERATIONS}${encoded_salt}${encoded_hash}"
