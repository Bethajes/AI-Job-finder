"""Best-effort Redis cache for admin dashboard stats (Week 8).

Every function is failure-tolerant: if Redis is unreachable, misconfigured
or simply not installed in the environment, calls degrade to a no-op and
callers fall back to computing stats directly. Caching must never be the
reason a request fails.
"""

import json
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "admin:stats:v1"

_client: Any = None
_client_checked = False


def _get_client() -> Any:
    """Lazily create the redis client; returns None when unavailable."""
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    try:
        import redis.asyncio as aioredis

        _client = aioredis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=0.5,
            socket_timeout=1.0,
            decode_responses=True,
        )
    except Exception:  # pragma: no cover - redis package missing
        logger.info("Redis cache unavailable; stats will not be cached")
        _client = None
    return _client


def stats_cache_key(*parts: Any) -> str:
    return ":".join([_KEY_PREFIX, *[str(p) for p in parts]])


async def cache_get_json(key: str) -> Optional[Any]:
    """Return the cached JSON value or None (miss / disabled / error)."""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception:
        logger.debug("Cache get failed for key=%s", key, exc_info=True)
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
    """Store a JSON-serializable value with a TTL. Returns True on success."""
    client = _get_client()
    if client is None:
        return False
    try:
        await client.set(
            key,
            json.dumps(value, default=str),
            ex=ttl_seconds or settings.STATS_CACHE_TTL,
        )
        return True
    except Exception:
        logger.debug("Cache set failed for key=%s", key, exc_info=True)
        return False


async def invalidate_stats_cache() -> None:
    """Drop every cached admin-stats entry (best effort)."""
    client = _get_client()
    if client is None:
        return
    try:
        keys = [key async for key in client.scan_iter(match=f"{_KEY_PREFIX}:*")]
        if keys:
            await client.delete(*keys)
    except Exception:
        logger.debug("Stats cache invalidation failed", exc_info=True)
