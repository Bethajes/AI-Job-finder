import uuid
from datetime import datetime
from typing import Any, Optional, Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ApplicationStatus
from app.models.application import Application
from app.models.company import Company
from app.models.job import Job
from app.models.user import User

# Eager-load everything responses and background tasks touch
# (job -> company -> owner, applicant -> profile) to avoid N+1 queries.
_LOAD_OPTIONS = (
    selectinload(Application.job)
    .selectinload(Job.company)
    .selectinload(Company.owner),
    selectinload(Application.applicant).selectinload(User.job_seeker_profile),
)


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── CRUD ────────────────────────────────────────────────────────────

    async def create(self, **fields: Any) -> Application:
        application = Application(**fields)
        self.session.add(application)
        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def get_by_id(self, application_id: uuid.UUID) -> Optional[Application]:
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(*_LOAD_OPTIONS)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_application_for_job(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> Optional[Application]:
        """Return the user's most recent application for a job (if any)."""
        result = await self.session.execute(
            select(Application)
            .where(
                Application.applicant_id == user_id,
                Application.job_id == job_id,
            )
            .order_by(Application.applied_at.desc(), Application.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, application: Application, **fields: Any) -> Application:
        for key, value in fields.items():
            if hasattr(application, key):
                setattr(application, key, value)
        await self.session.flush()
        return application

    # ── Listings ────────────────────────────────────────────────────────

    async def list_for_applicant(
        self,
        *,
        applicant_id: uuid.UUID,
        status: Optional[ApplicationStatus] = None,
        applied_after: Optional[datetime] = None,
        applied_before: Optional[datetime] = None,
        job_title: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Application], int]:
        """All applications of one job seeker, newest first."""
        conditions: list[Any] = [Application.applicant_id == applicant_id]
        conditions.extend(
            self._common_filters(
                status=status,
                applied_after=applied_after,
                applied_before=applied_before,
            )
        )
        if job_title:
            conditions.append(Application.job.has(Job.title.ilike(f"%{job_title}%")))

        total = await self._count(*conditions)

        result = await self.session.execute(
            select(Application)
            .where(*conditions)
            .options(*_LOAD_OPTIONS)
            .order_by(Application.applied_at.desc(), Application.id)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def list_for_company(
        self,
        *,
        company_id: uuid.UUID,
        job_id: Optional[uuid.UUID] = None,
        status: Optional[ApplicationStatus] = None,
        applied_after: Optional[datetime] = None,
        applied_before: Optional[datetime] = None,
        sort_by: str = "applied_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Application], int]:
        """Applications to any job owned by the company."""
        conditions: list[Any] = [
            Application.job.has(Job.company_id == company_id),
        ]
        if job_id is not None:
            conditions.append(Application.job_id == job_id)
        conditions.extend(
            self._common_filters(
                status=status,
                applied_after=applied_after,
                applied_before=applied_before,
            )
        )

        total = await self._count(*conditions)

        order_key = (
            Application.status
            if sort_by == "status"
            else Application.applied_at
        )
        if sort_order == "asc":
            order_clause = [order_key.asc(), Application.id]
        else:
            order_clause = [order_key.desc(), Application.id]

        result = await self.session.execute(
            select(Application)
            .where(*conditions)
            .options(*_LOAD_OPTIONS)
            .order_by(*order_clause)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    # ── Counters ────────────────────────────────────────────────────────

    async def increment_job_applications_count(self, job_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(applications_count=Job.applications_count + 1)
            .execution_options(synchronize_session=False)
        )
        await self.session.flush()

    async def decrement_job_applications_count(self, job_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Job)
            .where(Job.id == job_id)
            .values(applications_count=func.greatest(Job.applications_count - 1, 0))
            .execution_options(synchronize_session=False)
        )
        await self.session.flush()

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _common_filters(
        *,
        status: Optional[ApplicationStatus] = None,
        applied_after: Optional[datetime] = None,
        applied_before: Optional[datetime] = None,
    ) -> list[Any]:
        conditions: list[Any] = []
        if status is not None:
            conditions.append(Application.status == status)
        if applied_after is not None:
            conditions.append(Application.applied_at >= applied_after)
        if applied_before is not None:
            conditions.append(Application.applied_at <= applied_before)
        return conditions

    async def _count(self, *conditions: Any) -> int:
        result = await self.session.execute(
            select(func.count(Application.id)).where(*conditions)
        )
        return result.scalar_one()
