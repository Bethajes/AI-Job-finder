import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy import Select, func, select, update
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
        # Public browse never surfaces admin-hidden jobs (Week 8).
        conditions: list[Any] = [Job.status == status, Job.is_hidden.is_(False)]
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

    # ── Week 5: Full-text search, filtering, sorting ───────────────────

    @staticmethod
    def _build_tsquery(query_text: str) -> Any:
        """User-friendly tsquery: supports quoted phrases, OR and -exclusions."""
        return func.websearch_to_tsquery("english", query_text)

    def _apply_filters(
        self,
        stmt: Select,
        *,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        salary_min: Optional[Decimal] = None,
        salary_max: Optional[Decimal] = None,
        location: Optional[str] = None,
        is_remote: Optional[bool] = None,
        days_ago: Optional[int] = None,
        company_id: Optional[uuid.UUID] = None,
    ) -> Select:
        conditions: list[Any] = []
        if employment_type is not None:
            conditions.append(Job.employment_type == employment_type)
        if experience_level is not None:
            conditions.append(Job.experience_level == experience_level)
        # Salary overlap semantics:
        #   user_min -> job's advertised max must reach it
        #   user_max -> job's advertised min must not exceed it
        if salary_min is not None:
            conditions.append(Job.salary_max >= salary_min)
        if salary_max is not None:
            conditions.append(Job.salary_min <= salary_max)
        if location:
            conditions.append(Job.location.ilike(f"%{location}%"))
        if is_remote is not None:
            conditions.append(Job.is_remote.is_(is_remote))
        if days_ago is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_ago)
            conditions.append(Job.posted_date >= cutoff)
        if company_id is not None:
            conditions.append(Job.company_id == company_id)

        for condition in conditions:
            stmt = stmt.where(condition)
        return stmt

    @staticmethod
    def _order_clause(
        sort_by: str,
        sort_order: str,
        rank_expr: Optional[Any],
    ) -> list[Any]:
        descending = sort_order != "asc"
        if sort_by == "relevance" and rank_expr is not None:
            return [rank_expr.desc(), Job.posted_date.desc().nullslast()]
        column_map = {
            "posted_date": Job.posted_date,
            "salary_max": Job.salary_max,
            "salary_min": Job.salary_min,
        }
        column = column_map.get(sort_by, Job.posted_date)
        key = column.desc().nullslast() if descending else column.asc().nullsfirst()
        # Stable tiebreaker so pagination never duplicates/skips rows.
        return [key, Job.id]

    async def search_with_filters(
        self,
        *,
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
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[tuple[Job, Optional[float]]], int]:
        """Full-text search combined with structured filters.

        Returns (rows, total) where each row is ``(job, relevance_score)``;
        the score is ``None`` when no search query was supplied.
        """
        base_conditions: list[Any] = [
            Job.status == JobStatus.published,
            Job.is_hidden.is_(False),  # admin-hidden jobs stay out of search
        ]
        rank_expr: Optional[Any] = None
        tsquery: Optional[Any] = None
        if q:
            tsquery = self._build_tsquery(q)
            base_conditions.append(Job.search_vector.op("@@")(tsquery))
            rank_expr = func.ts_rank(Job.search_vector, tsquery).label("rank")

        filter_kwargs: dict[str, Any] = dict(
            employment_type=employment_type,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            location=location,
            is_remote=is_remote,
            days_ago=days_ago,
            company_id=company_id,
        )

        count_stmt = select(func.count(Job.id)).where(*base_conditions)
        count_stmt = self._apply_filters(count_stmt, **filter_kwargs)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = select(Job).where(*base_conditions)
        if rank_expr is not None:
            stmt = stmt.add_columns(rank_expr)
        stmt = stmt.options(selectinload(Job.company))
        stmt = self._apply_filters(stmt, **filter_kwargs)
        stmt = stmt.order_by(*self._order_clause(sort_by, sort_order, rank_expr))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        rows: list[tuple[Job, Optional[float]]] = []
        for row in result.all():
            job = row[0]
            score: Optional[float]
            score = float(row.rank) if q else None  # type: ignore[attr-defined]
            rows.append((job, score))
        return rows, total

    async def find_related_jobs(
        self,
        job: Job,
        *,
        limit: int = 5,
    ) -> Sequence[Job]:
        """Published jobs from the same company or with a similar title."""
        title_query = func.plainto_tsquery("english", job.title)
        same_company = Job.company_id == job.company_id
        similar_title = Job.search_vector.op("@@")(title_query)
        similarity_rank = func.ts_rank(Job.search_vector, title_query)

        stmt = (
            select(Job)
            .where(
                Job.id != job.id,
                Job.status == JobStatus.published,
                Job.is_hidden.is_(False),
                same_company | similar_title,
            )
            .options(selectinload(Job.company))
            .order_by(
                # Same-company matches first, then newest.
                same_company.desc(),
                similarity_rank.desc(),
                Job.posted_date.desc().nullslast(),
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

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
