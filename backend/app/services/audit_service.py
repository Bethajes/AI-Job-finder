"""Audit logging service (Week 8).

Admin mutations call `AuditService.log()` inside the same transaction as
the change itself, so every privileged action is recorded atomically with
its before/after diff and request context. A failed request rolls the log
entry back together with the failed change — the trail only ever contains
things that actually happened.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AdminActionType, AdminResourceType
from app.models.admin_log import AdminLog
from app.repositories.audit_repository import AuditRepository


def _json_safe(value: Any) -> Any:
    """Coerce common ORM/python types into JSON-serializable primitives."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value") and hasattr(type(value), "__members__"):  # enum
        return value.value
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)


def diff_changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[Any]]:
    """Build a {field: [old, new]} diff for audited scalar fields."""
    changes: dict[str, list[Any]] = {}
    for key, new_value in after.items():
        old_value = before.get(key)
        if old_value != new_value:
            changes[key] = [_json_safe(old_value), _json_safe(new_value)]
    return changes


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AuditRepository(session)

    async def log(
        self,
        *,
        admin_id: Optional[uuid.UUID],
        action_type: AdminActionType | str,
        resource_type: AdminResourceType | str,
        resource_id: Optional[uuid.UUID] = None,
        changes: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AdminLog:
        """Record one admin action (flushed; caller owns the commit)."""
        return await self.repository.create(
            admin_id=admin_id,
            action_type=(
                action_type.value if isinstance(action_type, AdminActionType)
                else str(action_type)
            ),
            resource_type=(
                resource_type.value if isinstance(resource_type, AdminResourceType)
                else str(resource_type)
            ),
            resource_id=resource_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )

    async def list_logs(
        self,
        *,
        admin_id: Optional[uuid.UUID] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[AdminLog], int]:
        return await self.repository.list_logs(
            admin_id=admin_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            start_date=start_date,
            end_date=end_date,
            offset=(page - 1) * limit,
            limit=limit,
        )
