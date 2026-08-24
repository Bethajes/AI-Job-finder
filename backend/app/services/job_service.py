import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.dependencies.company import ensure_can_manage_job, verify_company_ownership
from app.models.job import Job, JobStatus
from app.models.user import User
from app.repositories.job_repository import JobRepository

MAX_PAGE_SIZE = 100


def _validate_salary_range(
    salary_min: Optional[Decimal], salary_max: Optional[Decimal]
) -> None:
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        raise BadRequestException(detail="salary_min must be <= salary_max")


def _validate_deadline(deadline: Optional[datetime]) -> None:
    if deadline is None:
        return
    aware = deadline if deadline.tzinfo is not None else deadline.replace(tzinfo=timezone.utc)
    if aware <= datetime.now(timezone.utc):
        raise BadRequestException(detail="application_deadline must be in the future")


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = JobRepository(session)

    # ── Commands ────────────────────────────────────────────────────────

    async def create_job(self, *, user: User, data: dict[str, Any]) -> Job:
        company_id = data.pop("company_id")
        company = await verify_company_ownership(
            self.session, user=user, company_id=company_id
        )

        _validate_deadline(data.get("application_deadline"))
        _validate_salary_range(data.get("salary_min"), data.get("salary_max"))

        job = await self.repository.create(
            company_id=company.id,
            posted_by_id=user.id,
            status=JobStatus.draft,
            **data,
        )
        await self.session.commit()
        return await self._refetch(job.id)

    async def update_job(
        self,
        *,
        user: User,
        job_id: uuid.UUID,
        data: dict[str, Any],
    ) -> Job:
        job = await self._get_owned_job(user=user, job_id=job_id)

        if "application_deadline" in data:
            _validate_deadline(data["application_deadline"])

        merged_min = data.get("salary_min", job.salary_min)
        merged_max = data.get("salary_max", job.salary_max)
        _validate_salary_range(merged_min, merged_max)

        updated = await self.repository.update(job, **data)
        await self.session.commit()
        return await self._refetch(updated.id)

    async def publish_job(self, *, user: User, job_id: uuid.UUID) -> Job:
        job = await self._get_owned_job(user=user, job_id=job_id)
        if job.status == JobStatus.published:
            raise BadRequestException(detail="Job is already published")
        if job.application_deadline is not None:
            aware = (
                job.application_deadline
                if job.application_deadline.tzinfo is not None
                else job.application_deadline.replace(tzinfo=timezone.utc)
            )
            if aware <= datetime.now(timezone.utc):
                raise BadRequestException(
                    detail="Cannot publish a job whose application deadline has passed"
                )
        published = await self.repository.publish_job(job)
        await self.session.commit()
        return await self._refetch(published.id)

    async def close_job(self, *, user: User, job_id: uuid.UUID) -> Job:
        job = await self._get_owned_job(user=user, job_id=job_id)
        if job.status == JobStatus.closed:
            raise BadRequestException(detail="Job is already closed")
        closed = await self.repository.close_job(job)
        await self.session.commit()
        return await self._refetch(closed.id)

    async def delete_job(self, *, user: User, job_id: uuid.UUID) -> Job:
        """Soft delete: mark the job as closed instead of removing it."""
        job = await self._get_owned_job(user=user, job_id=job_id)
        soft_deleted = await self.repository.close_job(job)
        await self.session.commit()
        return await self._refetch(soft_deleted.id)

    # ── Queries ────────────────────────────────────────────────────────

    async def get_job_detail(
        self,
        job_id: uuid.UUID,
        *,
        viewer: Optional[User] = None,
        track_view: bool = True,
        include_related: bool = False,
        related_limit: int = 5,
    ) -> tuple[Job, Sequence[Job]]:
        """Fetch a job (visibility-checked) optionally with related openings."""
        job = await self.repository.get_by_id(job_id)
        if job is None:
            raise NotFoundException(detail="Job not found")

        if job.status != JobStatus.published and not self._is_owner(viewer, job):
            # Drafts/closed/expired jobs stay private to their owner.
            raise NotFoundException(detail="Job not found")

        if track_view and viewer is None:
            job.views_count += 1
            await self.session.commit()
            await self.session.refresh(job)

        related: Sequence[Job] = []
        if include_related and job.status == JobStatus.published:
            related = await self.repository.find_related_jobs(
                job, limit=related_limit
            )
        return job, related

    async def search_jobs(
        self,
        *,
        page: int = 1,
        limit: int = 20,
        q: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        salary_min: Optional[Decimal] = None,
        salary_max: Optional[Decimal] = None,
        location: Optional[str] = None,
        is_remote: Optional[bool] = None,
        days_ago: Optional[int] = None,
        company_id: Optional[uuid.UUID] = None,
        sort_by: str = "relevance",
        sort_order: str = "desc",
    ) -> tuple[list[tuple[Job, Optional[float]]], int]:
        """Public search over published jobs with filters, sorting, pagination.

        Relevance sorting requires a search query; without one it falls back
        to newest-first.
        """
        effective_sort_by = sort_by
        if not q and sort_by == "relevance":
            effective_sort_by = "posted_date"
            sort_order = "desc"

        offset = (page - 1) * limit
        return await self.repository.search_with_filters(
            q=q,
            employment_type=employment_type,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            location=location,
            is_remote=is_remote,
            days_ago=days_ago,
            company_id=company_id,
            sort_by=effective_sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=limit,
        )

    async def list_public_jobs(
        self,
        *,
        viewer: Optional[User] = None,
        page: int = 1,
        page_size: int = 20,
        company_id: Optional[uuid.UUID] = None,
        status: Optional[JobStatus] = None,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        location: Optional[str] = None,
        category: Optional[str] = None,
        is_remote: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[Sequence[Job], int]:
        effective_status = status or JobStatus.published

        if effective_status != JobStatus.published:
            # Only the owning employer may filter non-public statuses.
            if viewer is None or company_id is None:
                raise ForbiddenException(
                    detail="Filtering by non-published statuses requires owning the company"
                )
            await verify_company_ownership(
                self.session, user=viewer, company_id=company_id
            )

        offset = (page - 1) * page_size
        return await self.repository.list_jobs(
            company_id=company_id,
            status=effective_status,
            employment_type=employment_type,
            experience_level=experience_level,
            location=location,
            category=category,
            is_remote=is_remote,
            search=search,
            offset=offset,
            limit=page_size,
        )

    async def list_jobs_for_employer(
        self,
        *,
        user: User,
        company_id: uuid.UUID,
        status: Optional[JobStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Job], int]:
        await verify_company_ownership(
            self.session, user=user, company_id=company_id
        )
        offset = (page - 1) * page_size
        return await self.repository.list_by_company(
            company_id,
            status=status,
            offset=offset,
            limit=page_size,
        )

    async def get_company_active_jobs(
        self, *, user: User, company_id: uuid.UUID
    ) -> Sequence[Job]:
        await verify_company_ownership(
            self.session, user=user, company_id=company_id
        )
        return await self.repository.get_company_active_jobs(company_id)

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _is_owner(viewer: Optional[User], job: Job) -> bool:
        return viewer is not None and viewer.id == job.posted_by_id

    async def _get_owned_job(self, *, user: User, job_id: uuid.UUID) -> Job:
        job = await self.repository.get_by_id(job_id)
        if job is None:
            raise NotFoundException(detail="Job not found")
        await ensure_can_manage_job(self.session, user=user, job=job)
        return job

    async def _refetch(self, job_id: uuid.UUID) -> Job:
        """Reload a job with its company eagerly loaded for serialization."""
        job = await self.repository.get_by_id(job_id)
        if job is None:  # pragma: no cover - row was just written
            raise NotFoundException(detail="Job not found")
        return job
