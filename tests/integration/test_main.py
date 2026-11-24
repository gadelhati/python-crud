import pytest
from fastapi import Request, status

from app.main import service_error_handler
from app.services.base import ServiceError

pytestmark = pytest.mark.integration


def test_application_exposes_openapi_and_health(client) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert "/health" in schema["paths"]

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy"}


def test_root_endpoint_returns_expected_payload(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_service_error_handler_maps_known_codes() -> None:
    cases = {
        "not_found": status.HTTP_404_NOT_FOUND,
        "roles_not_found": status.HTTP_404_NOT_FOUND,
        "permissions_not_found": status.HTTP_404_NOT_FOUND,
        "invalid_credentials": status.HTTP_401_UNAUTHORIZED,
        "token_expired": status.HTTP_401_UNAUTHORIZED,
        "invalid_token": status.HTTP_401_UNAUTHORIZED,
        "forbidden": status.HTTP_403_FORBIDDEN,
        "account_locked": status.HTTP_423_LOCKED,
        "conflict": status.HTTP_409_CONFLICT,
        "integrity_error": status.HTTP_409_CONFLICT,
        "validation_error": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "invalid_operation": status.HTTP_400_BAD_REQUEST,
        "service_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    request = Request({"type": "http", "headers": []})

    for code, expected_status in cases.items():
        response = service_error_handler(request, ServiceError("test", code=code))
        assert response.status_code == expected_status


def test_service_error_handler_fails_closed_for_unknown_code() -> None:
    request = Request({"type": "http", "headers": []})
    response = service_error_handler(
        request,
        ServiceError("unknown", code="unmapped_error"),
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
