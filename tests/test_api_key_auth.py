"""
Tests for API key authentication (app/auth.py).

Covers:
- Requests with valid API key -> 200
- Requests with invalid API key -> 401
- Requests with missing API key -> 401
- Dev mode (no API_KEY configured) -> 200
- Constant-time comparison (hmac.compare_digest)
"""

import os
from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth import verify_api_key

TEST_KEY = "a" * 32  # meets minimum length requirement


def _make_app() -> FastAPI:
    """Create a minimal FastAPI app with the auth dependency."""
    app = FastAPI(dependencies=[Depends(verify_api_key)])

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client_with_key():
    """Test client with API_KEY configured."""
    with patch.dict(os.environ, {"API_KEY": TEST_KEY}):
        yield TestClient(_make_app())


@pytest.fixture
def client_no_key():
    """Test client with no API_KEY configured (dev mode)."""
    env = os.environ.copy()
    env.pop("API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        yield TestClient(_make_app())


# ============================================================================
# Tests: API key configured
# ============================================================================


class TestWithApiKey:
    """When API_KEY env var is set, requests must include the correct key."""

    def test_valid_key_returns_200(self, client_with_key: TestClient):
        resp = client_with_key.get("/test", headers={"X-API-Key": TEST_KEY})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_invalid_key_returns_401(self, client_with_key: TestClient):
        resp = client_with_key.get("/test", headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or missing API key"

    def test_missing_header_returns_401(self, client_with_key: TestClient):
        resp = client_with_key.get("/test")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid or missing API key"

    def test_empty_header_returns_401(self, client_with_key: TestClient):
        resp = client_with_key.get("/test", headers={"X-API-Key": ""})
        assert resp.status_code == 401


# ============================================================================
# Tests: No API key configured (dev mode)
# ============================================================================


class TestWithoutApiKey:
    """When API_KEY is not set, all requests are allowed (dev mode)."""

    def test_no_header_returns_200(self, client_no_key: TestClient):
        resp = client_no_key.get("/test")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_random_header_returns_200(self, client_no_key: TestClient):
        resp = client_no_key.get("/test", headers={"X-API-Key": "anything"})
        assert resp.status_code == 200


# ============================================================================
# Tests: Security properties
# ============================================================================


class TestSecurityProperties:
    """Verify constant-time comparison and logging."""

    def test_uses_hmac_compare_digest(self, client_with_key: TestClient):
        """Ensure hmac.compare_digest is called, not a plain == check."""
        with patch("app.auth.hmac.compare_digest", return_value=True) as mock_cmp:
            resp = client_with_key.get(
                "/test", headers={"X-API-Key": TEST_KEY}
            )
            assert resp.status_code == 200
            mock_cmp.assert_called_once_with(TEST_KEY, TEST_KEY)

    def test_rejected_request_is_logged(self, client_with_key: TestClient):
        """Failed auth attempts should be logged as warnings."""
        with patch("app.auth.logger") as mock_logger:
            resp = client_with_key.get(
                "/test", headers={"X-API-Key": "wrong"}
            )
            assert resp.status_code == 401
            mock_logger.warning.assert_called()
