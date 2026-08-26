"""Admin-specific queries: listings with filters + platform aggregations (Week 8)."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin_log import AdminLog
from app.models.application import Application
from app.models.company import Company
from app.models.job import Job
from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Users ───────────────────────────────────────────────────────────

    async def list_users(
        self,
        *,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[User], int]:
        conditions: list[Any] = []
        if search:
            pattern = f"%{search}%"
            conditions.append(
                User.email.ilike(pattern)
                | User.first_name.ilike(pattern)
                | User.last_name.ilike(pattern)
            )
        if role is not None:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active.is_(is_active))
        if is_verified is not None:
            conditions.append(User.is_verified.is_(is_verified))

        total = (
            await self.session.execute(
                select(func.count(User.id)).where(*conditions)
            )
        ).scalar_one()

        order_key = {
            "created_at": User.created_at,
            "last_login": User.last_login,
            "email": User.email,
        }.get(sort_by, User.created_at)
        order_clause = (
            [order_key.asc(), User.id]
            if sort_order == "asc"
            else [order_key.desc(), User.id]
        )

        result = await self.session.execute(
            select(User)
            .where(*conditions)
            .options(selectinload(User.companies))
            .order_by(*order_clause)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_user_application_stats(self, user_id: uuid.UUID) -> dict[str, int]:
        rows = await self.session.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.applicant_id == user_id)
            .group_by(Application.status)
        )
        by_status = {status.value if hasattr(status, "value") else str(status): count for status, count in rows.all()}
        return {"total": sum(by_status.values()), "by_status": by_status}

    async def get_employer_job_stats(self, user_id: uuid.UUID) -> dict[str, Any]:
        job_ids = (
            await self.session.execute(select(Job.id).where(Job.posted_by_id == user_id))
        ).scalars().all()
        if not job_ids:
            return {"total_jobs": 0, "total_applications_received": 0}
        apps = (
            await self.session.execute(
                select(func.count(Application.id)).where(Application.job_id.in_(job_ids))
            )
        ).scalar_one()
        return {"total_jobs": len(job_ids), "total_applications_received": apps}

    async def count_admins(self) -> int:
        return (
            await self.session.execute(
                select(func.count(User.id)).where(User.role == "admin")
            )
        ).scalar_one()

    # ── Companies ───────────────────────────────────────────────────────

    async def list_companies(
        self,
        *,
        search: Optional[str] = None,
        verification_status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Company], int]:
        conditions: list[Any] = []
        if search:
            pattern = f"%{search}%"
            conditions.append(Company.name.ilike(pattern) | Company.industry.ilike(pattern))
        if verification_status is not None:
            conditions.append(Company.verification_status == verification_status)
        if created_after is not None:
            conditions.append(Company.created_at >= created_after)
        if created_before is not None:
            conditions.append(Company.created_at <= created_before)

        total = (
            await self.session.execute(
                select(func.count(Company.id)).where(*conditions)
            )
        ).scalar_one()

        result = await self.session.execute(
            select(Company)
            .where(*conditions)
            .options(selectinload(Company.owner))
            .order_by(Company.created_at.desc(), Company.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_company_job_count(self, company_id: uuid.UUID) -> int:
        return (
            await self.session.execute(
                select(func.count(Job.id)).where(Job.company_id == company_id)
            )
        ).scalar_one()

    async def get_company_application_count(self, company_id: uuid.UUID) -> int:
        return (
            await self.session.execute(
                select(func.count(Application.id))
                .select_from(Application)
                .join(Job, Job.id == Application.job_id)
                .where(Job.company_id == company_id)
            )
        ).scalar_one()

    # ── Jobs ────────────────────────────────────────────────────────────

    async def list_jobs(
        self,
        *,
        status: Optional[str] = None,
        company_id: Optional[uuid.UUID] = None,
        flagged_only: bool = False,
        hidden_only: bool = False,
        search: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Job], int]:
        conditions: list[Any] = []
        if status is not None:
            conditions.append(Job.status == status)
        if company_id is not None:
            conditions.append(Job.company_id == company_id)
        if flagged_only:
            conditions.append(Job.is_flagged.is_(True))
        if hidden_only:
            conditions.append(Job.is_hidden.is_(True))
        if search:
            conditions.append(Job.title.ilike(f"%{search}%"))
        if created_after is not None:
            conditions.append(Job.created_at >= created_after)
        if created_before is not None:
            conditions.append(Job.created_at <= created_before)

        total = (
            await self.session.execute(select(func.count(Job.id)).where(*conditions))
        ).scalar_one()

        result = await self.session.execute(
            select(Job)
            .where(*conditions)
            .options(selectinload(Job.company))
            .order_by(Job.created_at.desc(), Job.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all(), total

    async def get_job_application_stats(self, job_id: uuid.UUID) -> dict[str, Any]:
        rows = await self.session.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.job_id == job_id)
            .group_by(Application.status)
        )
        by_status = {
            (status.value if hasattr(status, "value") else str(status)): count
            for status, count in rows.all()
        }
        return {"total": sum(by_status.values()), "by_status": by_status}

    # ── Dashboard stats ─────────────────────────────────────────────────

    @staticmethod
    def _count_grouped(stmt_result: Any) -> dict[str, int]:
        return {
            (key.value if hasattr(key, "value") else str(key)): count
            for key, count in stmt_result.all()
        }

    async def get_dashboard_stats(self) -> dict[str, Any]:
        users_by_role_rows = await self.session.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        jobs_by_status_rows = await self.session.execute(
            select(Job.status, func.count(Job.id)).group_by(Job.status)
        )
        apps_by_status_rows = await self.session.execute(
            select(Application.status, func.count(Application.id)).group_by(Application.status)
        )
        companies_by_verification_rows = await self.session.execute(
            select(Company.verification_status, func.count(Company.id))
            .group_by(Company.verification_status)
        )

        now = _utcnow()
        window_24h = now - timedelta(hours=24)
        window_7d = now - timedelta(days=7)
        window_30d = now - timedelta(days=30)

        async def _count(model: Any, column: Any, cutoff: datetime) -> int:
            return (
                await self.session.execute(
                    select(func.count(model.id)).where(column >= cutoff)
                )
            ).scalar_one()

        return {
            "total_users": (
                await self.session.execute(select(func.count(User.id)))
            ).scalar_one(),
            "users_by_role": self._count_grouped(users_by_role_rows),
            "total_jobs": (
                await self.session.execute(select(func.count(Job.id)))
            ).scalar_one(),
            "jobs_by_status": self._count_grouped(jobs_by_status_rows),
            "total_applications": (
                await self.session.execute(select(func.count(Application.id)))
            ).scalar_one(),
            "applications_by_status": self._count_grouped(apps_by_status_rows),
            "total_companies": (
                await self.session.execute(select(func.count(Company.id)))
            ).scalar_one(),
            "companies_by_verification": self._count_grouped(
                companies_by_verification_rows
            ),
            "new_users_7d": await _count(User, User.created_at, window_7d),
            "new_users_30d": await _count(User, User.created_at, window_30d),
            "new_jobs_7d": await _count(Job, Job.created_at, window_7d),
            "new_jobs_30d": await _count(Job, Job.created_at, window_30d),
            "active_users_24h": await self._active_users(window_24h),
            "active_users_7d": await self._active_users(window_7d),
        }

    async def _active_users(self, cutoff: datetime) -> int:
        return (
            await self.session.execute(
                select(func.count(User.id)).where(
                    User.last_login.is_not(None), User.last_login >= cutoff
                )
            )
        ).scalar_one()

    async def get_daily_growth(self, model: Any, days: int = 30) -> list[dict[str, Any]]:
        """Daily creation counts for the last `days` days (gap-filled)."""
        start = (_utcnow() - timedelta(days=days)).date()
        day_col = func.date(model.created_at)
        rows = await self.session.execute(
            select(day_col.label("day"), func.count(model.id))
            .where(day_col >= start)
            .group_by(day_col)
        )
        counts = {row.day: row[1] for row in rows.all()}
        series: list[dict[str, Any]] = []
        for offset in range(days + 1):
            day = start + timedelta(days=offset)
            series.append({"date": day.isoformat(), "count": counts.get(day, 0)})
        return series

    async def get_user_distribution(self) -> tuple[dict[str, int], dict[str, int]]:
        by_role_rows = await self.session.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        by_verification_rows = await self.session.execute(
            select(User.is_verified, func.count(User.id)).group_by(User.is_verified)
        )
        by_role = self._count_grouped(by_role_rows)
        by_verification = {
            ("verified" if verified else "unverified"): count
            for verified, count in by_verification_rows.all()
        }
        return by_role, by_verification

    async def get_job_trends(self) -> dict[str, Any]:
        categories_rows = await self.session.execute(
            select(Job.category, func.count(Job.id))
            .where(Job.category.is_not(None))
            .group_by(Job.category)
            .order_by(func.count(Job.id).desc())
            .limit(10)
        )
        type_rows = await self.session.execute(
            select(Job.employment_type, func.count(Job.id)).group_by(Job.employment_type)
        )

        avg_apps = (
            await self.session.execute(
                select(func.coalesce(func.avg(Job.applications_count), 0))
            )
        ).scalar_one()

        return {
            "popular_categories": [
                {"category": category or "uncategorized", "count": count}
                for category, count in categories_rows.all()
            ],
            "jobs_by_employment_type": self._count_grouped(type_rows),
            "average_applications_per_job": round(float(avg_apps or 0), 2),
        }

    # ── Reports ─────────────────────────────────────────────────────────

    async def get_user_activity_report(self) -> dict[str, Any]:
        now = _utcnow()
        windows = {
            "active_users_daily": now - timedelta(days=1),
            "active_users_weekly": now - timedelta(days=7),
            "active_users_monthly": now - timedelta(days=30),
        }
        activity: dict[str, int] = {}
        for name, cutoff in windows.items():
            activity[name] = await self._active_users(cutoff)

        applications_last_24h = (
            await self.session.execute(
                select(func.count(Application.id)).where(Application.applied_at >= windows["active_users_daily"])
            )
        ).scalar_one()
        applications_last_7d = (
            await self.session.execute(
                select(func.count(Application.id)).where(Application.applied_at >= windows["active_users_weekly"])
            )
        ).scalar_one()

        top_seekers_rows = await self.session.execute(
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                func.count(Application.id).label("activity_count"),
            )
            .join(Application, Application.applicant_id == User.id)
            .group_by(User.id)
            .order_by(func.count(Application.id).desc())
            .limit(10)
        )
        most_active = [
            {
                "user_id": str(row.id),
                "full_name": f"{row.first_name} {row.last_name}".strip(),
                "email": row.email,
                "activity_count": row.activity_count,
            }
            for row in top_seekers_rows.all()
        ]
        return {**activity, "applications_last_24h": applications_last_24h,
                "applications_last_7d": applications_last_7d,
                "most_active_users": most_active}

    async def get_job_performance_report(self) -> dict[str, Any]:
        top_jobs_rows = await self.session.execute(
            select(
                Job.id,
                Job.title,
                Company.name.label("company_name"),
                Job.applications_count,
            )
            .join(Company, Job.company_id == Company.id)
            .order_by(Job.applications_count.desc(), Job.created_at.asc())
            .limit(10)
        )
        top_jobs = [
            {
                "job_id": str(row.id),
                "title": row.title,
                "company_name": row.company_name,
                "applications_count": row.applications_count,
            }
            for row in top_jobs_rows.all()
        ]

        avg_apps = (
            await self.session.execute(
                select(func.coalesce(func.avg(Job.applications_count), 0))
            )
        ).scalar_one()

        # Average time-to-fill: posted_date -> first hired application.
        hired_rows = await self.session.execute(
            select(Application.applied_at, Job.posted_date)
            .join(Job, Application.job_id == Job.id)
            .where(Application.status == "hired", Job.posted_date.is_not(None))
        )
        durations_days = [
            (applied_at - posted_date).total_seconds() / 86400
            for applied_at, posted_date in hired_rows.all()
            if applied_at is not None and applied_at >= posted_date
        ]
        avg_fill = (
            round(sum(durations_days) / len(durations_days), 1) if durations_days else None
        )

        industry_rows = await self.session.execute(
            select(Company.industry, func.count(Job.id))
            .join(Company, Job.company_id == Company.id)
            .group_by(Company.industry)
        )
        type_rows = await self.session.execute(
            select(Job.employment_type, func.count(Job.id)).group_by(Job.employment_type)
        )

        return {
            "top_jobs_by_applications": top_jobs,
            "average_applications_per_job": round(float(avg_apps or 0), 2),
            "average_days_to_fill": avg_fill,
            "jobs_by_industry": {
                (industry or "unknown"): count for industry, count in industry_rows.all()
            },
            "jobs_by_employment_type": self._count_grouped(type_rows),
        }
