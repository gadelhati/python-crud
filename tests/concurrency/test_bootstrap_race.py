from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, engine
from app.main import app
from app.models.system_state import SystemState
from app.models.user import User
from app.services.permission import ServicePermission

pytestmark = pytest.mark.concurrency


@pytest.mark.concurrency
@pytest.mark.postgresql
def test_only_one_concurrent_bootstrap_request_succeeds(test_database) -> None:
    if engine.dialect.name != "postgresql":
        pytest.skip("Bootstrap race semantics are validated against PostgreSQL.")

    suffix = uuid4().hex
    payload = {
        "username": f"bootstrap_race_{suffix}",
        "email": f"bootstrap.race.{suffix}@example.com",
        "password": "BootstrapRacePassword123!",
        "first_name": "Race",
        "last_name": "Administrator",
    }

    with SessionLocal() as db:
        ServicePermission(db).sync_with_enum()
        state = db.get(SystemState, 1)
        if state is None:
            db.add(SystemState(id=1, bootstrap_completed=False))
        else:
            state.bootstrap_completed = False
        db.commit()

    try:

        def bootstrap() -> int:
            with TestClient(app) as worker:
                return worker.post(
                    "/admin/init/create-first-user",
                    json=payload,
                ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(lambda _: bootstrap(), range(2)))

        assert sorted(statuses) == [201, 409]

        with SessionLocal() as db:
            state = db.get(SystemState, 1)
            assert state is not None
            assert state.bootstrap_completed is True
            created = db.query(User).filter(User.username == payload["username"]).all()
            assert len(created) == 1
    finally:
        with SessionLocal() as db:
            created_users = db.query(User).filter(User.username == payload["username"]).all()
            for created_user in created_users:
                db.delete(created_user)
            state = db.get(SystemState, 1)
            if state is not None:
                state.bootstrap_completed = False
            db.commit()
