import os
from collections.abc import Generator
from uuid import uuid4

os.environ.setdefault("UVICORN_DATABASE_URL", "sqlite:///./db_test.sqlite3")
os.environ.setdefault(
    "UVICORN_JWT_SECRET_KEY",
    "test-secret-key-with-at-least-thirty-two-characters",
)
os.environ.setdefault(
    "UVICORN_JWT_REFRESH_SECRET_KEY",
    "test-refresh-secret-key-with-at-least-thirty-two-chars",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import SessionLocal, engine
from app.main import app
from app.models.base import Base
from app.models.role import Role
from app.models.user import User
from app.services.password import hash_password


def _reset_postgres_schema() -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None]:
    is_pg = engine.dialect.name == "postgresql"
    if is_pg:
        _reset_postgres_schema()
    else:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    if is_pg:
        _reset_postgres_schema()
    else:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def authentication_headers(
    application_client: TestClient,
    username: str,
    password: str,
) -> dict[str, str]:
    response = application_client.post(
        "/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.json()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client: TestClient) -> Generator[dict[str, str]]:
    """Cria um usuário administrador no banco para autenticar requisições administrativas."""
    unique_suffix = uuid4().hex[:8]
    username = f"seed_admin_{unique_suffix}"
    password = "SeedAdminPassword123!"

    with SessionLocal() as db:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role is None:
            admin_role = Role(
                name="admin",
                description="System administrator",
                is_default=False,
                is_system=True,
            )
            db.add(admin_role)
            db.flush()

        admin = User(
            username=username,
            email=f"seed.{unique_suffix}@example.com",
            password=hash_password(password),
            first_name="Seed",
            last_name="Admin",
            roles=[admin_role],
        )
        db.add(admin)
        db.commit()
        admin_id = admin.id

    headers = authentication_headers(client, username, password)
    yield headers

    with SessionLocal() as db:
        stored_admin = db.get(User, admin_id)
        if stored_admin is not None:
            db.delete(stored_admin)
            db.commit()
