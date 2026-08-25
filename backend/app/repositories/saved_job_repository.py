"""SavedJob CRUD operations (Week 7)."""

import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import Job
from app.models.saved_job import SavedJob

_LOAD_OPTIONS = (
    selectinload(SavedJob.job).selectinload(Job.company),
)


class SavedJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_saved_job(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> Optional[SavedJob]:
        result = await self.session.execute(
            select(SavedJob).where(
                SavedJob.user_id == user_id,
                SavedJob.job_id == job_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_saved_job(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> Optional[SavedJob]:
        result = await self.session.execute(
            select(SavedJob).where(
                SavedJob.user_id == user_id,
                SavedJob.job_id == job_id,
                SavedJob.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, job_id: uuid.UUID) -> SavedJob:
        saved_job = SavedJob(user_id=user_id, job_id=job_id)
        self.session.add(saved_job)
        await self.session.flush()
        await self.session.refresh(saved_job)
        return saved_job

    async def reactivate(self, saved_job: SavedJob) -> SavedJob:
        saved_job.is_active = True
        await self.session.flush()
        return saved_job

    async def deactivate(self, saved_job: SavedJob) -> SavedJob:
        saved_job.is_active = False
        await self.session.flush()
        return saved_job

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[SavedJob], int]:
        conditions: list[Any] = [
            SavedJob.user_id == user_id,
            SavedJob.is_active.is_(True),
        ]

        total = await self._count(*conditions)

        result = await self.session.execute(
            select(SavedJob)
            .where(*conditions)
            .options(*_LOAD_OPTIONS)
            .order_by(SavedJob.created_at.desc(), SavedJob.id)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def _count(self, *conditions: Any) -> int:
        result = await self.session.execute(
            select(func.count(SavedJob.id)).where(*conditions)
        )
        return result.scalar_one()
