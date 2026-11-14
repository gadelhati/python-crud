import base64
import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_SIZE = 16


def _derive(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str) -> str:
    """Returns a PBKDF2-HMAC-SHA256 hash suitable for database storage."""
    salt = secrets.token_bytes(_SALT_SIZE)
    digest = _derive(password, salt, _ITERATIONS)
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{_ALGORITHM}${_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_password(password: str, stored_password: str) -> bool:
    """Checks a plaintext password against a stored hash. Malformed hashes return False."""
    try:
        algorithm, iterations, encoded_salt, encoded_digest = stored_password.split("$")
        if algorithm != _ALGORITHM:
            return False
        salt = base64.urlsafe_b64decode(encoded_salt)
        expected = base64.urlsafe_b64decode(encoded_digest)
        actual = _derive(password, salt, int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(actual, expected)
