"""Week 7: Device-token management and notification-preference endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User, DEFAULT_NOTIFICATION_PREFERENCES
from app.schemas.notification import (
    DeviceTokenActionResponse,
    DeviceTokenCreate,
    DeviceTokenRemove,
    NotificationPreferences,
    NotificationPreferencesUpdate,
)
from app.services.notification_service import PushNotificationService

router = APIRouter(tags=["notifications"])


def _get_push_service(session: AsyncSession) -> PushNotificationService:
    return PushNotificationService(session)


# ── Device tokens ───────────────────────────────────────────────────────


@router.post("/device-tokens", status_code=201, response_model=DeviceTokenActionResponse)
async def register_device_token(
    body: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DeviceTokenActionResponse:
    """Register (or update) a device token for push notifications."""
    svc = _get_push_service(session)
    device_token = await svc.save_device_token(
        user_id=current_user.id,
        token=body.device_token,
        device_type=body.device_type,
    )
    await session.commit()
    return DeviceTokenActionResponse(
        id=device_token.id,
        device_type=device_token.device_type,
        message="Device token registered",
    )


@router.delete("/device-tokens", response_model=DeviceTokenActionResponse)
async def remove_device_token(
    body: DeviceTokenRemove,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DeviceTokenActionResponse:
    """Remove a device token (e.g. on logout or app uninstall)."""
    import uuid as _uuid

    svc = _get_push_service(session)
    removed = await svc.remove_device_token(
        user_id=current_user.id,
        token=body.device_token,
    )
    await session.commit()
    return DeviceTokenActionResponse(
        id=_uuid.uuid4() if not removed else _uuid.uuid4(),
        device_type="",
        message="Device token removed" if removed else "Device token not found",
    )


# ── Notification preferences ───────────────────────────────────────────


@router.get("/users/me/notification-preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
) -> NotificationPreferences:
    """Get the current user's notification preferences."""
    stored = current_user.notification_preferences or {}
    merged = dict(DEFAULT_NOTIFICATION_PREFERENCES)
    merged.update(stored)
    return NotificationPreferences(**merged)


@router.put("/users/me/notification-preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    body: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NotificationPreferences:
    """Update notification preferences (partial update)."""
    stored = current_user.notification_preferences or {}
    merged = dict(DEFAULT_NOTIFICATION_PREFERENCES)
    merged.update(stored)

    updates = body.model_dump(exclude_unset=True)
    merged.update(updates)

    current_user.notification_preferences = merged
    session.add(current_user)
    await session.commit()

    return NotificationPreferences(**merged)
