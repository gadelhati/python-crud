from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, engine
from app.main import app
from app.models.user import User
from app.services.password import hash_password

pytestmark = pytest.mark.concurrency


@pytest.mark.concurrency
@pytest.mark.postgresql
def test_refresh_token_can_only_be_rotated_once(test_database) -> None:
    if engine.dialect.name != "postgresql":
        pytest.skip("Refresh-token race semantics are validated against PostgreSQL.")

    suffix = uuid4().hex
    username = f"refresh_race_{suffix}"
    password = "RefreshRacePassword123!"

    with SessionLocal() as db:
        user = User(
            username=username,
            email=f"refresh.race.{suffix}@example.com",
            password=hash_password(password),
        )
        db.add(user)
        db.commit()
        user_id = user.id

    try:
        with TestClient(app) as client:
            login = client.post(
                "/login",
                json={"username": username, "password": password},
            )
            assert login.status_code == 200, login.text
            refresh_token = login.json()["refresh_token"]

            def rotate() -> int:
                with TestClient(app) as worker:
                    return worker.post(
                        "/login/refresh",
                        json={"refresh_token": refresh_token},
                    ).status_code

            with ThreadPoolExecutor(max_workers=2) as pool:
                statuses = list(pool.map(lambda _: rotate(), range(2)))

        assert sorted(statuses) == [200, 401]
    finally:
        with SessionLocal() as db:
            stored = db.get(User, user_id)
            if stored is not None:
                db.delete(stored)
                db.commit()
