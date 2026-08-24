import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobStatus


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── CRUD ────────────────────────────────────────────────────────────

    async def create(self, **fields: Any) -> Job:
        job = Job(**fields)
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def get_by_id(
        self,
        job_id: uuid.UUID,
        *,
        load_company: bool = True,
    ) -> Optional[Job]:
        stmt = select(Job).where(Job.id == job_id)
        if load_company:
            stmt = stmt.options(selectinload(Job.company))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, job: Job, **fields: Any) -> Job:
        for key, value in fields.items():
            if hasattr(job, key):
                setattr(job, key, value)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def delete(self, job: Job) -> None:
        await self.session.delete(job)
        await self.session.flush()

    # ── Listing ────────────────────────────────────────────────────────

    async def list_by_company(
        self,
        company_id: uuid.UUID,
        *,
        status: Optional[JobStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Job], int]:
        conditions = [Job.company_id == company_id]
        if status is not None:
            conditions.append(Job.status == status)

        count_result = await self.session.execute(
            select(func.count(Job.id)).where(*conditions)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Job)
            .options(selectinload(Job.company))
            .where(*conditions)
            .order_by(Job.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_company_active_jobs(
        self,
        company_id: uuid.UUID,
    ) -> Sequence[Job]:
        result = await self.session.execute(
            select(Job)
            .options(selectinload(Job.company))
            .where(
                Job.company_id == company_id,
                Job.status == JobStatus.published,
            )
            .order_by(Job.posted_date.desc().nullslast())
        )
        return result.scalars().all()

    async def list_jobs(
        self,
        *,
        company_id: Optional[uuid.UUID] = None,
        status: JobStatus = JobStatus.published,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
        is_remote: Optional[bool] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Job], int]:
        conditions: list[Any] = [Job.status == status]
        if company_id is not None:
            conditions.append(Job.company_id == company_id)
        if employment_type is not None:
            conditions.append(Job.employment_type == employment_type)
        if experience_level is not None:
            conditions.append(Job.experience_level == experience_level)
        if category is not None:
            conditions.append(Job.category.ilike(category))
        if is_remote is not None:
            conditions.append(Job.is_remote.is_(is_remote))
        if location is not None:
            conditions.append(Job.location.ilike(f"%{location}%"))
        if search:
            pattern = f"%{search}%"
            conditions.append(
                Job.title.ilike(pattern) | Job.description.ilike(pattern)
            )

        count_result = await self.session.execute(
            select(func.count(Job.id)).where(*conditions)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Job)
            .options(selectinload(Job.company))
            .where(*conditions)
            .order_by(Job.is_featured.desc(), Job.posted_date.desc().nullslast())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    # ── Status management ──────────────────────────────────────────────

    async def publish_job(self, job: Job) -> Job:
        now = datetime.now(timezone.utc)
        job.status = JobStatus.published
        if job.posted_date is None:
            job.posted_date = now
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def close_job(self, job: Job) -> Job:
        now = datetime.now(timezone.utc)
        job.status = JobStatus.closed
        if job.closing_date is None:
            job.closing_date = now
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def expire_overdue_jobs(self, *, now: Optional[datetime] = None) -> int:
        """Mark published jobs whose deadline has passed as expired."""
        current = now or datetime.now(timezone.utc)
        result = await self.session.execute(
            update(Job)
            .where(
                Job.status == JobStatus.published,
                Job.application_deadline.is_not(None),
                Job.application_deadline < current,
            )
            .values(status=JobStatus.expired, closing_date=current)
            .execution_options(synchronize_session=False)
        )
        await self.session.flush()
        return result.rowcount or 0

    # ── Counters (used from Week 6 onwards) ────────────────────────────

    async def increment_views(self, job_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(views_count=Job.views_count + 1)
            .execution_options(synchronize_session=False)
        )
        await self.session.flush()
