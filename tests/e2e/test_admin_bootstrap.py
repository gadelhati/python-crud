import pytest

from app.models.system_state import SystemState

pytestmark = pytest.mark.e2e


def test_first_admin_bootstrap_is_one_time_operation(
    client,
    db_session,
) -> None:
    # Arrange: ensure the bootstrap is available.
    state = db_session.get(SystemState, 1)

    if state is None:
        state = SystemState(
            id=1,
            bootstrap_completed=False,
        )
        db_session.add(state)
    else:
        state.bootstrap_completed = False

    db_session.flush()

    payload = {
        "username": "first_admin_e2e",
        "email": "first.admin.e2e@example.com",
        "password": "FirstAdminPassword123!",
        "first_name": "First",
        "last_name": "Administrator",
    }

    # Act: perform the first bootstrap request.
    first = client.post(
        "/admin/init/create-first-user",
        json=payload,
    )

    # Assert: the first request must create the administrator.
    assert first.status_code == 201, first.text
    assert any(role["name"] == "admin" for role in first.json()["roles"])

    # Act: attempt a second bootstrap request.
    second = client.post(
        "/admin/init/create-first-user",
        json=payload,
    )

    # Assert: subsequent bootstrap requests must be rejected.
    assert second.status_code == 409

    # Assert: reload the state after the HTTP requests.
    db_session.refresh(state)
    assert state.bootstrap_completed is True
