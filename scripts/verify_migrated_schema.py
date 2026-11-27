"""Verify that the application works against the Alembic-migrated schema."""

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import inspect

# Validate the test database configuration before importing the application.
from tests.config import backend

if backend != "postgresql":
    raise RuntimeError("Migration integration checks require PostgreSQL.")

from app.database import engine
from app.main import app


def verify_migration_revision() -> None:
    """Ensure the database is upgraded to the current Alembic head."""
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    expected_revision = script.get_current_head()

    with engine.connect() as connection:
        actual_revision = MigrationContext.configure(connection).get_current_revision()

    if actual_revision != expected_revision:
        raise RuntimeError(
            f"Database revision mismatch: expected {expected_revision}, got {actual_revision}."
        )


def verify_migrated_tables() -> None:
    """Ensure the migration-created schema contains the required tables and columns."""
    required_columns = {
        "users": {"id", "username", "email", "auth_version"},
        "roles": {"id", "name"},
        "permissions": {"id", "name", "action"},
        "password_reset_tokens": {"id", "user_id", "token_hash"},
        "revoked_tokens": {"jti", "user_id"},
        "system_state": {"id", "bootstrap_completed"},
    }

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    for table, expected_columns in required_columns.items():
        if table not in tables:
            raise RuntimeError(f"Missing migrated table: {table}")

        actual_columns = {column["name"] for column in inspector.get_columns(table)}
        missing_columns = expected_columns - actual_columns

        if missing_columns:
            raise RuntimeError(f"Table '{table}' is missing columns: {sorted(missing_columns)}")


def verify_application_startup() -> None:
    """Ensure application startup and a basic HTTP request work with the migrated schema."""
    with TestClient(app) as client:
        response = client.get("/health")

    if response.status_code != 200:
        raise RuntimeError(
            f"Application health check failed: {response.status_code} - {response.text}"
        )


def main() -> None:
    verify_migration_revision()
    verify_migrated_tables()
    verify_application_startup()
    print("PostgreSQL migration integration checks passed.")


if __name__ == "__main__":
    main()
