from uuid import uuid4

import pytest

from app.services.base import ServiceError
from app.services.user import ServiceUser

pytestmark = pytest.mark.unit


def test_service_base_rejects_too_many_ids(db_session) -> None:
    service = ServiceUser(db_session)

    with pytest.raises(ServiceError, match="Cannot have more than"):
        service._validate_ids([uuid4(), uuid4()], max_items=1, label="roles")


def test_service_base_rejects_duplicate_ids(db_session) -> None:
    service = ServiceUser(db_session)
    identifier = uuid4()

    with pytest.raises(ServiceError, match="Duplicate"):
        service._validate_ids([identifier, identifier], max_items=5, label="roles")


def test_service_base_rejects_missing_entities(db_session) -> None:
    service = ServiceUser(db_session)

    with pytest.raises(ServiceError, match="not found"):
        service._check_found([], [uuid4()], label="roles")
