import pytest

from tests.conftest import authentication_headers

pytestmark = pytest.mark.security


def test_user_can_read_own_record_but_not_other_user(client, user_factory) -> None:
    owner = user_factory(password="OwnerPassword123!")
    other = user_factory(password="OtherPassword123!")
    owner_headers = authentication_headers(client, owner.username, "OwnerPassword123!")

    own = client.get(f"/user/{owner.id}", headers=owner_headers)
    assert own.status_code == 200

    other_response = client.get(f"/user/{other.id}", headers=owner_headers)
    assert other_response.status_code == 403


def test_regular_user_cannot_list_users_or_access_audit(client, user_factory) -> None:
    regular = user_factory(password="RegularPassword123!")
    headers = authentication_headers(client, regular.username, "RegularPassword123!")

    assert client.get("/user", headers=headers).status_code == 403
    assert client.get("/user/audit", headers=headers).status_code == 403
