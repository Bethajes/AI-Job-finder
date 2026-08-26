"""Tests for the Week 12 rate limiter (app/core/rate_limit.py)."""

import pytest
from fastapi import HTTPException

from app.core import rate_limit
from app.core.config import settings


def make_request(ip: str = "10.0.0.1"):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "client": (ip, 12345),
        "query_string": b"",
    }
    from starlette.requests import Request

    return Request(scope)


@pytest.fixture(autouse=True)
def _reset_memory_windows():
    rate_limit._memory_windows.clear()
    yield
    rate_limit._memory_windows.clear()


@pytest.mark.asyncio
async def test_rate_limit_disabled_by_default(monkeypatch):
    """In development the limiter is a no-op regardless of volume."""
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", False)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    request = make_request()
    for _ in range(50):
        await rate_limit.enforce_rate_limit(request, "test")


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_threshold(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)
    # Force the in-memory fallback path (no Redis in unit tests).
    monkeypatch.setattr(rate_limit, "_redis", lambda: None)
    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 3)

    request = make_request()
    for _ in range(3):
        await rate_limit.enforce_rate_limit(request, "test")

    with pytest.raises(HTTPException) as exc_info:
        await rate_limit.enforce_rate_limit(request, "test")
    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers


@pytest.mark.asyncio
async def test_rate_limit_is_per_client_ip(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)
    monkeypatch.setattr(rate_limit, "_redis", lambda: None)
    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 2)

    first = make_request("10.0.0.1")
    second = make_request("10.0.0.2")

    await rate_limit.enforce_rate_limit(first, "test")
    await rate_limit.enforce_rate_limit(first, "test")

    # A different IP is unaffected by the first client's usage.
    await rate_limit.enforce_rate_limit(second, "test")
