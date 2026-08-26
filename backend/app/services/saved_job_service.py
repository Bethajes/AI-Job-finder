"""Business logic for the saved-jobs feature (Week 7)."""

import logging
import uuid
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApplicationStatus  # noqa: F401 – kept available for consumers
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.job import Job, JobStatus
from app.repositories.saved_job_repository import SavedJobRepository

logger = logging.getLogger(__name__)


class SavedJobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SavedJobRepository(session)

    async def save_job(self, *, user_id: uuid.UUID, job_id: uuid.UUID) -> tuple[dict, bool]:
        """Save a job for a user.

        Returns ``(saved_job, is_new)`` where *is_new* is ``True`` when a
        fresh row was created (as opposed to a reactivation).

        Raises ``NotFoundException`` when the job does not exist and
        ``BadRequestException`` when it is not published.
        """
        await self._ensure_published_job(job_id)

        existing = await self.repository.get_saved_job(user_id, job_id)
        if existing is not None:
            if existing.is_active:
                raise ConflictException(detail="Job is already saved")
            # Reactivate a previously unsaved entry
            await self.repository.reactivate(existing)
            await self.session.commit()
            logger.info("Job %s re-saved by user %s", job_id, user_id)
            return existing, False

        saved_job = await self.repository.create(user_id=user_id, job_id=job_id)
        await self.session.commit()
        logger.info("Job %s saved by user %s", job_id, user_id)
        return saved_job, True

    async def unsave_job(self, *, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        """Unsave a job (soft-delete).  Returns True if a job was unsaved."""
        saved_job = await self.repository.get_saved_job(user_id, job_id)
        if saved_job is None or not saved_job.is_active:
            return False

        await self.repository.deactivate(saved_job)
        await self.session.commit()
        logger.info("Job %s unsaved by user %s", job_id, user_id)
        return True

    async def list_saved_jobs(
        self,
        *,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence, int]:
        return await self.repository.list_for_user(
            user_id=user_id,
            offset=(page - 1) * limit,
            limit=limit,
        )

    async def _ensure_published_job(self, job_id: uuid.UUID) -> Job:
        """Validate that a job exists and is published."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.company))
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundException(detail="Job not found")
        if job.status != JobStatus.published:
            raise BadRequestException(detail="This job is not open for applications")
        return job
