"""Pydantic schemas for device tokens and notification preferences (Week 7)."""

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


DeviceTypeLiteral = Literal["ios", "android", "web"]


# ── Device tokens ───────────────────────────────────────────────────────


class DeviceTokenCreate(BaseModel):
    device_token: str = Field(min_length=1, max_length=4096)
    device_type: DeviceTypeLiteral = "android"


class DeviceTokenRemove(BaseModel):
    device_token: str = Field(min_length=1, max_length=4096)


class DeviceTokenView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_type: str
    created_at: datetime


class DeviceTokenActionResponse(BaseModel):
    id: uuid.UUID
    device_type: str
    message: str


# ── Notification preferences ────────────────────────────────────────────

# Defaults kept in sync with app.models.user.DEFAULT_NOTIFICATION_PREFERENCES


class NotificationPreferences(BaseModel):
    application_updates: bool = True
    new_jobs: bool = True
    marketing: bool = False
    in_app: bool = True


class NotificationPreferencesUpdate(BaseModel):
    """Partial update: only supplied fields are merged."""

    model_config = ConfigDict(extra="forbid")

    application_updates: Optional[bool] = None
    new_jobs: Optional[bool] = None
    marketing: Optional[bool] = None
    in_app: Optional[bool] = None
