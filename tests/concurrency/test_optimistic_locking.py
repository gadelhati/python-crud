from uuid import uuid4

import pytest
from sqlalchemy.orm.exc import StaleDataError

from app.database import SessionLocal
from app.models.user import User

pytestmark = pytest.mark.concurrency


def test_optimistic_locking_rejects_stale_update(test_database) -> None:
    suffix = uuid4().hex
    with SessionLocal() as setup:
        user = User(
            username=f"concurrent_{suffix}",
            email=f"concurrent.{suffix}@example.com",
            password="already-hashed-test-value",
        )
        setup.add(user)
        setup.commit()
        user_id = user.id

    try:
        with SessionLocal() as session_one, SessionLocal() as session_two:
            first = session_one.get(User, user_id)
            second = session_two.get(User, user_id)
            assert first is not None
            assert second is not None

            first.first_name = "FirstWriter"
            session_one.commit()

            second.first_name = "StaleWriter"
            with pytest.raises(StaleDataError):
                session_two.commit()
            session_two.rollback()

        with SessionLocal() as verify:
            stored = verify.get(User, user_id)
            assert stored is not None
            assert stored.first_name == "FirstWriter"
            assert stored.version_id == 2
    finally:
        with SessionLocal() as cleanup:
            stored = cleanup.get(User, user_id)
            if stored is not None:
                cleanup.delete(stored)
                cleanup.commit()
