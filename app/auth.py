"""API key authentication for the WorkbenchIQ backend."""

from __future__ import annotations

import hmac
import logging
import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

_MIN_KEY_LENGTH = 32


def _get_api_key() -> str | None:
    """Return the configured API key (cached after first read)."""
    return os.getenv("API_KEY") or None


async def verify_api_key(
    api_key: str | None = Security(_API_KEY_HEADER),
) -> None:
    """FastAPI dependency that validates the X-API-Key header.

    Behaviour:
    - If ``API_KEY`` env var is **not set**: all requests are allowed
      (backwards-compatible development mode).
    - If ``API_KEY`` is set but the request header is missing or wrong:
      returns 401 Unauthorized.

    Uses ``hmac.compare_digest`` for constant-time comparison to prevent
    timing attacks.
    """
    expected = _get_api_key()

    if expected is None:
        # Dev mode – no key configured, allow everything.
        return

    if api_key is None:
        logger.warning("Rejected request: missing X-API-Key header")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    if not hmac.compare_digest(api_key, expected):
        logger.warning("Rejected request: invalid API key")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
