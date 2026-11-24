"""Shared fixtures with transaction isolation for API and service tests."""

from collections.abc import Callable, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app

# Import all mapped models before touching Base.metadata.
from app.models.base import Base
from app.models.role import Role
from app.models.user import User
from app.rate_limit import limiter
from app.services.password import hash_password

# Configure the test environment before importing the application.
from tests.config import backend


def _assert_test_engine(test_engine: Engine) -> None:
    """Fail closed if the engine does not match the explicitly approved test target."""
    actual = test_engine.url
    if actual.get_backend_name() != backend:
        raise RuntimeError("Application engine differs from the validated test backend.")

    if backend == "sqlite":
        if actual.database not in {"./db_test.sqlite3", "db_test.sqlite3"}:
            raise RuntimeError("Refusing destructive setup on a non-test SQLite database.")
    elif backend == "postgresql" and (
        actual.database != "app_test" or actual.host not in {"localhost", "127.0.0.1"}
    ):
        raise RuntimeError("Refusing destructive setup on a non-test PostgreSQL database.")


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Generator[None]:
    """Create a disposable schema only after validating the database identity."""
    _assert_test_engine(engine)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_connection(test_database):
    """One outer transaction per test; application sessions join via savepoints."""
    connection = engine.connect()
    outer_transaction = connection.begin()
    try:
        yield connection
    finally:
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()


@pytest.fixture
def db_session(db_connection) -> Generator[Session]:
    """Session for direct service/model assertions, rolled back after each test."""
    session = Session(
        bind=db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_connection) -> Generator[TestClient]:
    """HTTP client whose request sessions share the test's outer transaction."""

    def override_get_db() -> Generator[Session]:
        session = Session(
            bind=db_connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def concurrent_client(test_database) -> Generator[TestClient]:
    """HTTP client using real independent SessionLocal connections.

    Use only in concurrency tests; unlike `client`, requests are not wrapped in
    the per-test outer transaction.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Prevent SlowAPI counters from leaking between tests."""
    limiter.reset()


@pytest.fixture
def auth_headers(client: TestClient, db_session: Session) -> dict[str, str]:
    """Create an administrator inside the test transaction and authenticate it."""
    suffix = uuid4().hex
    username = f"test_admin_{suffix}"
    password = "TestAdminPassword123!"

    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    if admin_role is None:
        admin_role = Role(
            name="admin",
            description="Test administrator",
            is_default=False,
            is_system=True,
        )
        db_session.add(admin_role)
        db_session.flush()

    admin = User(
        username=username,
        email=f"test.admin.{suffix}@example.com",
        password=hash_password(password),
        first_name="Test",
        last_name="Administrator",
        roles=[admin_role],
    )
    db_session.add(admin)
    db_session.flush()

    response = client.post(
        "/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def user_factory(db_session: Session) -> Callable[..., User]:
    """Create a user in the current test transaction."""

    def factory(
        *,
        username: str | None = None,
        email: str | None = None,
        password: str = "UserPassword123!",
        roles: list[Role] | None = None,
        is_active: bool = True,
    ) -> User:
        suffix = uuid4().hex
        user = User(
            username=username or f"user_{suffix}",
            email=email or f"user.{suffix}@example.com",
            password=hash_password(password),
            first_name="Test",
            last_name="User",
            is_active=is_active,
            roles=roles or [],
        )
        db_session.add(user)
        db_session.flush()
        return user

    return factory


@pytest.fixture
def role_factory(db_session: Session) -> Callable[..., Role]:
    """Create a non-system role in the current test transaction."""

    def factory(
        *,
        name: str | None = None,
        permissions: list | None = None,
        is_default: bool = False,
        is_system: bool = False,
    ) -> Role:
        role = Role(
            name=name or f"role_{uuid4().hex}",
            description="Test role",
            permissions=permissions or [],
            is_default=is_default,
            is_system=is_system,
        )
        db_session.add(role)
        db_session.flush()
        return role

    return factory


@pytest.fixture
def permission_factory(db_session: Session):
    """Return an existing enum permission or create it for the current test."""
    from app.models.permission import Permission

    def factory(action):
        permission = db_session.query(Permission).filter(Permission.action == action).first()
        if permission is None:
            permission = Permission(name=action.value, action=action)
            db_session.add(permission)
            db_session.flush()
        return permission

    return factory


def authentication_headers(
    application_client: TestClient,
    username: str,
    password: str,
) -> dict[str, str]:
    response = application_client.post(
        "/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
