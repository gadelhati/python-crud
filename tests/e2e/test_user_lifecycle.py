from uuid import uuid4

import pytest

pytestmark = pytest.mark.e2e

pytestmark = pytest.mark.e2e


def test_complete_user_lifecycle(client, auth_headers) -> None:
    suffix = uuid4().hex
    payload = {
        "username": f"lifecycle_{suffix}",
        "email": f"lifecycle.{suffix}@example.com",
        "password": "LifecyclePassword123!",
        "first_name": "Lifecycle",
        "last_name": "Test",
    }

    created = client.post("/user", json=payload, headers=auth_headers)
    assert created.status_code == 201, created.text
    user_id = created.json()["id"]

    try:
        fetched = client.get(f"/user/{user_id}", headers=auth_headers)
        assert fetched.status_code == 200
        assert fetched.json()["username"] == payload["username"]

        updated = client.put(
            f"/user/{user_id}",
            json={
                "username": payload["username"],
                "email": payload["email"],
                "first_name": "Updated",
                "last_name": "Lifecycle",
            },
            headers=auth_headers,
        )
        assert updated.status_code == 200
        assert updated.json()["first_name"] == "Updated"

        assert client.delete(f"/user/{user_id}", headers=auth_headers).status_code == 204
        assert (
            client.patch(
                f"/user/{user_id}/restore",
                headers=auth_headers,
            ).status_code
            == 200
        )
    finally:
        client.delete(f"/user/{user_id}/hard", headers=auth_headers)
