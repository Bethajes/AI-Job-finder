"""Audit log persistence (Week 8)."""

import uuid
from datetime import datetime
from typing import Any, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin_log import AdminLog
from app.models.user import User


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **fields: Any) -> AdminLog:
        entry = AdminLog(**fields)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_logs(
        self,
        *,
        admin_id: Optional[uuid.UUID] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[AdminLog], int]:
        conditions: list[Any] = []
        if admin_id is not None:
            conditions.append(AdminLog.admin_id == admin_id)
        if action_type is not None:
            conditions.append(AdminLog.action_type == action_type)
        if resource_type is not None:
            conditions.append(AdminLog.resource_type == resource_type)
        if resource_id is not None:
            conditions.append(AdminLog.resource_id == resource_id)
        if start_date is not None:
            conditions.append(AdminLog.created_at >= start_date)
        if end_date is not None:
            conditions.append(AdminLog.created_at <= end_date)

        total = (
            await self.session.execute(
                select(func.count(AdminLog.id)).where(*conditions)
            )
        ).scalar_one()

        result = await self.session.execute(
            select(AdminLog)
            .where(*conditions)
            .options(selectinload(AdminLog.admin).load_only(User.email))
            .order_by(AdminLog.created_at.desc(), AdminLog.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total
