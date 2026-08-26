"""Best-effort rate limiting for sensitive endpoints (Week 12).

A fixed-window limiter keyed by client IP + scope. Counts are stored in
Redis when available and in a per-process fallback otherwise, so the API
keeps working (just without cross-worker limits) if Redis is down.

Enforcement is enabled when `ENABLE_RATE_LIMIT` is true, or automatically
in production (`APP_ENV=production`). In development/tests it is a no-op so
local flows and the test suite are never throttled.
"""

import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)

_memory_windows: dict[str, list[float]] = defaultdict(list)


def _enabled() -> bool:
    if settings.ENABLE_RATE_LIMIT:
        return True
    return settings.APP_ENV == "production"


def _redis() -> Any | None:
    """Reuse the stats-cache Redis client when reachable."""
    try:
        from app.core import cache

        return cache._get_client()
    except Exception:  # pragma: no cover - defensive
        return None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(request: Request, scope: str) -> None:
    """Raise 429 when the caller exceeds the configured window."""
    if not _enabled():
        return

    key = f"ratelimit:{scope}:{_client_ip(request)}"
    max_requests = max(1, settings.RATE_LIMIT_REQUESTS)
    period = max(1, settings.RATE_LIMIT_PERIOD)
    now = time.monotonic()

    client = _redis()
    count = -1
    ttl = period
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            result = await pipe.execute()
            count = int(result[0])
            if result[1] is None or int(result[1]) < 0:
                await client.expire(key, period)
                ttl = period
            else:
                ttl = int(result[1])
        except Exception:
            logger.debug("Rate-limit Redis path failed; using memory", exc_info=True)
            client = None

    if client is None:
        # In-process fallback (per worker).
        window = _memory_windows[key]
        cutoff = now - period
        while window and window[0] < cutoff:
            window.pop(0)
        window.append(now)
        count = len(window)

    if count > max_requests:
        logger.warning(
            "RATE-LIMIT exceeded scope=%s ip=%s count=%d", scope, key.rsplit(":", 1)[-1], count
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down.",
            headers={"Retry-After": str(max(1, ttl))},
        )


def rate_limit(scope: str):
    """FastAPI dependency factory, e.g. `Depends(rate_limit("admin"))`."""

    async def dependency(request: Request) -> None:
        await enforce_rate_limit(request, scope)

    return Depends(dependency)
