"""Admin business logic (Week 8).

Conventions follow the existing services: repositories flush, this layer
commits, domain errors come from app.core.exceptions. Every mutating
method writes an AdminLog entry in the same transaction via AuditService,
so the audit trail is atomic with the change it describes.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import cache
from app.core.enums import (
    AdminActionType,
    AdminResourceType,
    VerificationStatus,
)
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.repositories.admin_repository import AdminRepository
from app.services.audit_service import AuditService, diff_changes

logger = logging.getLogger(__name__)

_SORTABLE_USER_FIELDS = {"created_at", "last_login", "email"}


def _ensure_aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AdminRepository(session)
        self.audit = AuditService(session)

    # ── User management ─────────────────────────────────────────────────

    async def list_users(
        self,
        *,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[User], int]:
        if sort_by not in _SORTABLE_USER_FIELDS:
            raise BadRequestException(detail=f"Cannot sort users by '{sort_by}'")
        return await self.repository.list_users(
            search=search,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=(page - 1) * limit,
            limit=limit,
        )

    async def get_user_detail(self, user_id: uuid.UUID) -> User:
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.job_seeker_profile),
                selectinload(User.companies),
            )
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundException(detail="User not found")
        return user

    async def update_user(
        self,
        *,
        admin: User,
        user_id: uuid.UUID,
        data: dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """Change role / activation / verification on a user account."""
        user = await self.get_user_detail(user_id)

        before = {
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }

        if user.id == admin.id:
            if data.get("role") is not None:
                raise BadRequestException(detail="Admins cannot change their own role")
            if data.get("is_active") is False:
                raise BadRequestException(detail="Admins cannot deactivate themselves")

        updates: dict[str, Any] = {}
        for field in ("role", "is_active", "is_verified"):
            if data.get(field) is not None:
                updates[field] = data[field]
        if "role" in updates and user.role == UserRole.admin:
            other_admin_count = await self.repository.count_admins()
            if other_admin_count <= 1:
                raise BadRequestException(
                    detail="Cannot demote the only remaining admin"
                )

        updated = self._apply(user, updates)

        changes = diff_changes(before, {k: getattr(updated, k) for k in updates})
        await self.audit.log(
            admin_id=admin.id,
            action_type=AdminActionType.USER_UPDATE,
            resource_type=AdminResourceType.USER,
            resource_id=user.id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        logger.info("ADMIN user=%s updated user=%s %s", admin.id, user.id, changes)
        return await self.get_user_detail(user.id)

    async def delete_user(
        self,
        *,
        admin: User,
        user_id: uuid.UUID,
        hard: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict[str, Any]:
        """Soft-delete by default (deactivate); hard delete cascades data."""
        if user_id == admin.id:
            raise BadRequestException(detail="Admins cannot delete their own account")

        user = await self.get_user_detail(user_id)

        if hard:
            if user.role == UserRole.admin:
                raise ForbiddenException(detail="Admin accounts cannot be hard-deleted")
            detail_msg = f"User {user.email} permanently deleted"
            await self.session.delete(user)
        else:
            detail_msg = f"User {user.email} deactivated"
            user.is_active = False

        await self.audit.log(
            admin_id=admin.id,
            action_type=AdminActionType.USER_DELETE,
            resource_type=AdminResourceType.USER,
            resource_id=user_id,
            changes={"mode": "hard" if hard else "soft"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        logger.info("ADMIN user=%s deleted user=%s hard=%s", admin.id, user_id, hard)
        return {"id": user_id, "detail": detail_msg}

    async def verify_user_email(
        self,
        *,
        admin: User,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """Manually mark a user's email as verified."""
        user = await self.get_user_detail(user_id)
        user.is_verified = True
        if hasattr(user, "email_verified_at"):
            user.email_verified_at = datetime.now(timezone.utc)

        await self.audit.log(
            admin_id=admin.id,
            action_type=AdminActionType.USER_VERIFY,
            resource_type=AdminResourceType.USER,
            resource_id=user.id,
            changes={"is_verified": [False, True]},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        logger.info("ADMIN user=%s verified email of user=%s", admin.id, user.id)
        return await self.get_user_detail(user.id)

    # ── Company management ──────────────────────────────────────────────

    async def list_companies(
        self,
        *,
        search: Optional[str] = None,
        verification_status: Optional[VerificationStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Company], int]:
        if created_after and created_before:
            if _ensure_aware(created_after) > _ensure_aware(created_before):
                raise BadRequestException(
                    detail="created_after must be before created_before"
                )
        return await self.repository.list_companies(
            search=search,
            verification_status=(
                verification_status.value if verification_status else None
            ),
            created_after=_ensure_aware(created_after),
            created_before=_ensure_aware(created_before),
            offset=(page - 1) * limit,
            limit=limit,
        )

    async def get_company_detail(self, company_id: uuid.UUID) -> Company:
        company = await self._get_company(company_id)
        company.job_count = await self.repository.get_company_job_count(company_id)  # type: ignore[attr-defined]
        company.total_applications = (  # type: ignore[attr-defined]
            await self.repository.get_company_application_count(company_id)
        )
        return company

    async def verify_company(
        self,
        *,
        admin: User,
        company_id: uuid.UUID,
        status: VerificationStatus | str,
        admin_notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Company:
        """Approve / reject / reset a company's verification."""
        company = await self._get_company(company_id)
        new_status = (
            status if isinstance(status, VerificationStatus) else VerificationStatus(status)
        )

        before_status = company.verification_status or VerificationStatus.PENDING.value
        company.verification_status = new_status.value
        company.is_verified = new_status == VerificationStatus.APPROVED
        company.verified_at = (
            datetime.now(timezone.utc)
            if new_status == VerificationStatus.APPROVED
            else None
        )
        if admin_notes is not None:
            company.admin_notes = admin_notes

        await self.audit.log(
            admin_id=admin.id,
            action_type=AdminActionType.COMPANY_VERIFY,
            resource_type=AdminResourceType.COMPANY,
            resource_id=company.id,
            changes={
                "verification_status": [before_status, new_status.value],
                **({"admin_notes": admin_notes} if admin_notes else {}),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        logger.info(
            "ADMIN user=%s set company=%s verification to %s",
            admin.id, company.id, new_status.value,
        )
        return await self.get_company_detail(company.id)

    async def delete_company(
        self,
        *,
        admin: User,
        company_id: uuid.UUID,
        hard: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict[str, Any]:
        """Suspend (soft) or cascade-delete (hard) a company."""
        company = await self._get_company(company_id)
        name = company.name

        if hard:
            detail_msg = f"Company {name} permanently deleted"
            await self.session.delete(company)
        else:
            company.is_active = False
            detail_msg = f"Company {name} suspended"

        await self.audit.log(
            admin_id=admin.id,
            action_type=AdminActionType.COMPANY_DELETE,
            resource_type=AdminResourceType.COMPANY,
            resource_id=company_id,
            changes={"mode": "hard" if hard else "soft"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        logger.info(
            "ADMIN user=%s deleted company=%s hard=%s", admin.id, company_id, hard
        )
        return {"id": company_id, "detail": detail_msg}

    # ── Job moderation ──────────────────────────────────────────────────

    async def list_jobs(
        self,
        *,
        status: Optional[JobStatus] = None,
        company_id: Optional[uuid.UUID] = None,
        flagged_only: bool = False,
        hidden_only: bool = False,
        search: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Job], int]:
        return await self.repository.list_jobs(
            status=status.value if status else None,
            company_id=company_id,
            flagged_only=flagged_only,
            hidden_only=hidden_only,
            search=search,
            created_after=_ensure_aware(created_after),
            created_before=_ensure_aware(created_before),
            offset=(page - 1) * limit,
            limit=limit,
        )

    async def get_job_detail(self, job_id: uuid.UUID) -> Job:
        result = await self.session.execute(
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.company))
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundException(detail="Job not found")
        job.application_stats = await self.repository.get_job_application_stats(job_id)  # type: ignore[attr-defined]
        return job

    async def moderate_job(
        self,
        *,
        admin: User,
        job_id: uuid.UUID,
        action: str,
        admin_notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Job:
        """Approve / reject / flag / unflag / hide / unhide a posting."""
        job = await self._get_job(job_id)

        before = {
            "status": job.status.value if hasattr(job.status, "value") else str(job.status),
            "is_hidden": job.is_hidden,
            "is_flagged": job.is_flagged,
        }
        now = datetime.now(timezone.utc)
        updates: dict[str, Any] = {}

        if action == "approve":
            # Approval restores full visibility (clears flag and hide).
            updates["status"] = JobStatus.published
            updates["is_flagged"] = False
            updates["is_hidden"] = False
        elif action == "reject":
            updates["status"] = JobStatus.closed
        elif action == "flag":
            updates["is_flagged"] = True
            updates["flagged_at"] = now
        elif action == "unflag":
            updates["is_flagged"] = False
        elif action == "hide":
            updates["is_hidden"] = True
        elif action == "unhide":
            updates["is_hidden"] = False
        else:
            raise BadRequestException(detail=f"Unknown moderation action '{action}'")

        if admin_notes is not None:
            updates["admin_notes"] = admin_notes

        updated = self._apply(job, updates)

        changes = diff_changes(before, {k: getattr(updated, k) for k in updates})
        await self.audit.log(
            admin_id=admin.id,
            action_type=AdminActionType.JOB_MODERATE,
            resource_type=AdminResourceType.JOB,
            resource_id=job.id,
            changes={"action": action, **changes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        await cache.invalidate_stats_cache()
        logger.info(
            "ADMIN user=%s moderated job=%s action=%s %s",
            admin.id, job.id, action, changes,
        )
        return await self.get_job_detail(job.id)

    async def delete_job(
        self,
        *,
        admin: User,
        job_id: uuid.UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict[str, Any]:
        """Remove an inappropriate job (applications cascade)."""
        job = await self._get_job(job_id)
        title = job.title
        await self.session.delete(job)

        await self.audit.log(
            admin_id=admin.id,
            action_type=AdminActionType.JOB_DELETE,
            resource_type=AdminResourceType.JOB,
            resource_id=job_id,
            changes={"title": title},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        await cache.invalidate_stats_cache()
        logger.info("ADMIN user=%s deleted job=%s", admin.id, job_id)
        return {"id": job_id, "detail": f"Job '{title}' deleted"}

    # ── Stats & reports ─────────────────────────────────────────────────

    async def get_dashboard_stats(self) -> dict[str, Any]:
        cache_key = cache.stats_cache_key("dashboard")
        cached = await cache.cache_get_json(cache_key)
        if cached is not None:
            return cached
        stats = await self.repository.get_dashboard_stats()
        stats["generated_at"] = datetime.now(timezone.utc).isoformat()
        await cache.cache_set_json(cache_key, stats)
        return stats

    async def get_user_stats(self) -> dict[str, Any]:
        cache_key = cache.stats_cache_key("users")
        cached = await cache.cache_get_json(cache_key)
        if cached is not None:
            return cached
        growth_daily = await self.repository.get_daily_growth(User, days=30)
        by_role, by_verification = await self.repository.get_user_distribution()
        stats = {
            "growth_daily": growth_daily,
            "distribution_by_role": by_role,
            "distribution_by_verification": by_verification,
        }
        await cache.cache_set_json(cache_key, stats)
        return stats

    async def get_job_stats(self) -> dict[str, Any]:
        cache_key = cache.stats_cache_key("jobs")
        cached = await cache.cache_get_json(cache_key)
        if cached is not None:
            return cached
        trends = await self.repository.get_job_trends()
        trends["posting_trend_daily"] = await self.repository.get_daily_growth(Job, days=30)
        await cache.cache_set_json(cache_key, trends)
        return trends

    async def get_user_activity_report(self) -> dict[str, Any]:
        return await self.repository.get_user_activity_report()

    async def get_job_performance_report(self) -> dict[str, Any]:
        return await self.repository.get_job_performance_report()

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _apply(obj: Any, updates: dict[str, Any]) -> Any:
        for key, value in updates.items():
            setattr(obj, key, value)
        return obj

    async def _get_company(self, company_id: uuid.UUID) -> Company:
        result = await self.session.execute(
            select(Company)
            .where(Company.id == company_id)
            .options(selectinload(Company.owner))
        )
        company = result.scalar_one_or_none()
        if company is None:
            raise NotFoundException(detail="Company not found")
        return company

    async def _get_job(self, job_id: uuid.UUID) -> Job:
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundException(detail="Job not found")
        return job
