from uuid import uuid4

import pytest

from app.models.user import User
from app.services.password import hash_password
from tests.conftest import authentication_headers

pytestmark = pytest.mark.integration


def test_audit_endpoints_are_admin_only(client, auth_headers, db_session) -> None:
    suffix = uuid4().hex
    regular = User(
        username=f"audit_regular_{suffix}",
        email=f"audit.regular.{suffix}@example.com",
        password=hash_password("RegularPassword123!"),
    )
    db_session.add(regular)
    db_session.flush()
    regular_headers = authentication_headers(
        client,
        regular.username,
        "RegularPassword123!",
    )

    for endpoint in ("/user/audit", "/role/audit", "/permission/audit"):
        assert client.get(endpoint, headers=regular_headers).status_code == 403
        response = client.get(endpoint, headers=auth_headers)
        assert response.status_code == 200, response.text
        assert isinstance(response.json()["items"], list)


def test_soft_deleted_user_remains_visible_in_audit(client, auth_headers) -> None:
    suffix = uuid4().hex
    payload = {
        "username": f"audit_target_{suffix}",
        "email": f"audit.target.{suffix}@example.com",
        "password": "AuditPassword123!",
        "first_name": "Audit",
        "last_name": "Target",
    }
    created = client.post("/user", json=payload, headers=auth_headers)
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    try:
        assert client.delete(f"/user/{user_id}", headers=auth_headers).status_code == 204
        audit = client.get(f"/user/audit/{user_id}", headers=auth_headers)
        assert audit.status_code == 200, audit.text
        assert audit.json()["deleted_at"] is not None
        assert audit.json()["deleted_by"] is not None
        assert audit.json()["created_by"] is not None
    finally:
        client.delete(f"/user/{user_id}/hard", headers=auth_headers)
