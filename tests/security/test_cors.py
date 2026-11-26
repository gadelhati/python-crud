"""Tests for CORS middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

ALLOWED_ORIGINS = ["https://frontend.example.com"]
ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = ["Authorization", "Content-Type"]


def create_test_client() -> TestClient:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
    )

    @app.get("/resource")
    def get_resource() -> dict[str, str]:
        return {"message": "success"}

    return TestClient(app)


def test_cors_allows_configured_origin() -> None:
    client = create_test_client()

    response = client.get(
        "/resource",
        headers={"Origin": ALLOWED_ORIGINS[0]},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGINS[0]


def test_cors_rejects_unconfigured_origin() -> None:
    client = create_test_client()

    response = client.get(
        "/resource",
        headers={"Origin": "https://unauthorized.example.com"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_preflight_request() -> None:
    client = create_test_client()

    response = client.options(
        "/resource",
        headers={
            "Origin": ALLOWED_ORIGINS[0],
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGINS[0]
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
    assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_cors_rejects_disallowed_preflight_method() -> None:
    client = create_test_client()

    response = client.options(
        "/resource",
        headers={
            "Origin": ALLOWED_ORIGINS[0],
            "Access-Control-Request-Method": "DELETE-ALL",
        },
    )

    assert response.status_code == 400


def test_cors_rejects_disallowed_preflight_header() -> None:
    client = create_test_client()

    response = client.options(
        "/resource",
        headers={
            "Origin": ALLOWED_ORIGINS[0],
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Unauthorized-Header",
        },
    )

    assert response.status_code == 400
