"""Fail-closed configuration for the test process.

Set PYTEST_DATABASE_URL to a dedicated local test database when PostgreSQL is used.
The application's normal UVICORN_DATABASE_URL and .env file are intentionally ignored.
"""

import os

from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "PYTEST_DATABASE_URL",
    "sqlite:///./db_test.sqlite3",
)

url = make_url(TEST_DATABASE_URL)
backend = url.get_backend_name()

if backend == "sqlite":
    # Do not allow :memory:, arbitrary paths, or the application's normal db.sqlite3.
    if url.database not in {"./db_test.sqlite3", "db_test.sqlite3"}:
        raise RuntimeError(
            "SQLite tests must use exactly sqlite:///./db_test.sqlite3. "
            "Set PYTEST_DATABASE_URL explicitly if needed."
        )
elif backend == "postgresql":
    if url.database != "app_test" or url.host not in {"localhost", "127.0.0.1"}:
        raise RuntimeError("PostgreSQL tests are restricted to the local database 'app_test'.")
else:
    raise RuntimeError(f"Unsupported test database backend: {backend}")

# Override, rather than setdefault: values from a developer's .env must not win.
os.environ["UVICORN_DATABASE_URL"] = TEST_DATABASE_URL
os.environ["UVICORN_JWT_SECRET_KEY"] = "pytest-access-secret-key-only-for-local-tests-2026"
os.environ["UVICORN_JWT_REFRESH_SECRET_KEY"] = "pytest-refresh-secret-key-only-for-local-tests-2026"
