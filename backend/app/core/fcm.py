"""Firebase Cloud Messaging (FCM) integration.

Lazily initializes the Firebase Admin SDK.  When ``FIREBASE_CREDENTIALS_PATH``
is empty or the ``firebase-admin`` package is not installed, push notifications
are silently skipped with a warning log — the rest of the application continues
to work without restrictions.

All functions here are **safe to call from background tasks**: errors are caught
and logged, never propagated.
"""

import logging
import threading
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Lazy Firebase initialisation ────────────────────────────────────────

_lock = threading.Lock()
_initialized = False
_fcm_available = False

try:
    import firebase_admin  # type: ignore[import-untyped]
    from firebase_admin import credentials, messaging  # type: ignore[import-untyped]

    _fcm_available = True
except ImportError:
    firebase_admin = None  # type: ignore[assignment]
    messaging = None  # type: ignore[assignment]


def _ensure_initialized() -> bool:
    """Initialise the Firebase app exactly once.  Returns True when ready."""
    global _initialized
    if _initialized:
        return True

    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    if not cred_path:
        logger.info("FIREBASE_CREDENTIALS_PATH is empty – push notifications disabled")
        return False

    if not _fcm_available:
        logger.warning("firebase-admin is not installed – push notifications disabled")
        return False

    with _lock:
        if _initialized:
            return True
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            _initialized = True
            logger.info("Firebase Admin SDK initialised")
            return True
        except Exception:
            logger.exception("Failed to initialise Firebase Admin SDK")
            return False


# ── Synchronous send helper (blocking) ──────────────────────────────────


def send_push_notification_sync(
    device_tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Send a push notification to one or more devices.

    This is a **blocking** function (FCM SDK is synchronous).  Run it inside
    ``asyncio.to_thread`` or ``BackgroundTasks`` (which handles that).

    Returns a summary dict:
        {"sent": int, "failed": int, "invalid_tokens": list[str]}
    """
    summary: dict[str, Any] = {"sent": 0, "failed": 0, "invalid_tokens": []}

    if not _ensure_initialized():
        return summary

    if not device_tokens:
        return summary

    # Truncate to protect FCM limits (notification body <= 4 KB, title <= 256 B)
    title = title[:200]
    body = body[:3000]

    # FCM data payload values must be plain strings (not dicts).
    str_data: dict[str, str] = {}
    if data:
        for k, v in data.items():
            str_data[str(k)] = str(v)

    # Build messages — send in batches of 100 (FCM limit is ~500 per call,
    # but 100 keeps memory and error surface manageable).
    messages = []
    for token in device_tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=str_data or None,
            token=token,
        )
        messages.append(message)

    BATCH_SIZE = 100
    for i in range(0, len(messages), BATCH_SIZE):
        batch = messages[i : i + BATCH_SIZE]
        batch_tokens = device_tokens[i : i + BATCH_SIZE]
        try:
            response = messaging.send_each(batch)
            for j, send_response in enumerate(response.responses):
                if send_response.success:
                    summary["sent"] += 1
                else:
                    summary["failed"] += 1
                    err = send_response.exception
                    # FCM invalidates tokens when the app is uninstalled or the
                    # token rotates — remove them from our database.
                    if err is not None and _is_unregistered_error(err):
                        summary["invalid_tokens"].append(batch_tokens[j])
        except Exception:
            logger.exception("FCM batch send failed (tokens=%d)", len(batch))
            summary["failed"] += len(batch)

    return summary


def _is_unregistered_error(exc: Exception) -> bool:
    """Return True if *exc* indicates a permanently invalid device token."""
    # The exception class path changed across firebase-admin versions.
    exc_name = type(exc).__name__
    if exc_name in ("UnregisteredError", "ThirdPartyAuthError"):
        return True
    # Also catch the common messaging error message pattern.
    msg = str(exc).lower()
    return "unregistered" in msg or "not registered" in msg


# ── Async wrapper for background task use ────────────────────────────────


async def send_push_notification(
    device_tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Async wrapper around :func:`send_push_notification_sync`.

    Offloads the blocking FCM call to a thread so the event loop stays free.
    """
    import asyncio

    return await asyncio.get_event_loop().run_in_executor(
        None, send_push_notification_sync, device_tokens, title, body, data
    )
