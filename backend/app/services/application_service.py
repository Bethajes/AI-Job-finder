import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    EMPLOYER_STATUS_TRANSITIONS,
    TERMINAL_STATUSES,
    ApplicationSource,
    ApplicationStatus,
)
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.application import Application
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.repositories.application_repository import ApplicationRepository
from app.services.upload_service import upload_service

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ApplicationRepository(session)

    # ── Commands ────────────────────────────────────────────────────────

    async def submit_application(
        self,
        *,
        user: User,
        job_id: uuid.UUID,
        resume_file: Any,
        cover_letter: Optional[str] = None,
        source: ApplicationSource = ApplicationSource.WEB,
        ip_address: Optional[str] = None,
        additional_documents: Optional[list[dict[str, str]]] = None,
    ) -> Application:
        """Validate and record a new job application (uploads the resume)."""
        if user.role != UserRole.job_seeker:
            raise ForbiddenException(detail="Only job seekers can apply to jobs")

        job = await self._get_open_job(job_id)

        existing = await self.repository.get_user_application_for_job(
            user.id, job.id
        )
        if existing is not None and existing.status not in (
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        ):
            raise ConflictException(
                detail=(
                    "You have already applied to this job. "
                    "You can re-apply only if your previous application "
                    "was rejected or withdrawn."
                )
            )

        # Upload happens before the DB write so a failed upload never
        # leaves an application row pointing at a missing file.
        resume_url = await upload_service.upload_resume(
            file=resume_file, user_id=str(user.id)
        )

        application = await self.repository.create(
            job_id=job.id,
            applicant_id=user.id,
            status=ApplicationStatus.APPLIED,
            cover_letter=(cover_letter or "").strip() or None,
            resume_url=resume_url,
            additional_documents=additional_documents or [],
            source=source,
            ip_address=ip_address,
        )
        await self.repository.increment_job_applications_count(job.id)
        await self.session.commit()
        logger.info(
            "Application %s created for job=%s by applicant=%s",
            application.id,
            job.id,
            user.id,
        )
        return await self._refetch(application.id)

    async def update_application_status(
        self,
        *,
        user: User,
        application_id: uuid.UUID,
        data: dict[str, Any],
    ) -> Application:
        """Employer-driven status transition with validation and audit log."""
        application = await self._get_application_managed_by(user, application_id)

        current_status: ApplicationStatus = ApplicationStatus(application.status)
        if isinstance(data["status"], ApplicationStatus):
            new_status = data["status"]
        else:
            new_status = ApplicationStatus(data["status"])

        if current_status == new_status:
            raise BadRequestException(
                detail=f"Application is already '{current_status.value}'"
            )

        allowed = EMPLOYER_STATUS_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise BadRequestException(
                detail=(
                    f"Invalid status transition: '{current_status.value}' "
                    f"cannot move to '{new_status.value}'"
                )
            )

        fields: dict[str, Any] = {
            "status": new_status,
            "status_change_count": application.status_change_count + 1,
        }
        changed_at = _utcnow()

        if new_status == ApplicationStatus.VIEWED and application.viewed_at is None:
            fields["viewed_at"] = changed_at

        if data.get("interview_date") is not None:
            interview_date = _ensure_aware(data["interview_date"])
            if interview_date is not None and interview_date <= changed_at:
                raise BadRequestException(
                    detail="interview_date must be in the future"
                )
            fields["interview_date"] = interview_date

        if data.get("employer_notes") is not None:
            fields["employer_notes"] = data["employer_notes"]

        updated = await self.repository.update(application, **fields)
        await self.session.commit()

        # Audit trail: log every status change with a timestamp.
        logger.info(
            "APPLICATION_STATUS_CHANGE application=%s job=%s '%s' -> '%s' "
            "at=%s by_employer=%s",
            application.id,
            application.job_id,
            current_status.value,
            new_status.value,
            changed_at.isoformat(),
            user.id,
        )
        return await self._refetch(updated.id)

    async def withdraw_application(
        self, *, user: User, application_id: uuid.UUID
    ) -> Application:
        """Applicant-initiated withdrawal from an active application."""
        application = await self._get_application_of_applicant(user, application_id)

        current_status = ApplicationStatus(application.status)
        if current_status in TERMINAL_STATUSES:
            if current_status == ApplicationStatus.WITHDRAWN:
                raise BadRequestException(detail="Application is already withdrawn")
            raise BadRequestException(
                detail=(
                    f"A '{current_status.value}' application cannot be withdrawn"
                )
            )

        updated = await self.repository.update(
            application,
            status=ApplicationStatus.WITHDRAWN,
            status_change_count=application.status_change_count + 1,
        )
        await self.session.commit()
        logger.info(
            "APPLICATION_WITHDRAWN application=%s at=%s by_applicant=%s",
            application.id,
            _utcnow().isoformat(),
            user.id,
        )
        return await self._refetch(updated.id)

    # ── Queries ────────────────────────────────────────────────────────

    async def get_application_for_viewer(
        self, *, user: User, application_id: uuid.UUID
    ) -> tuple[Application, bool]:
        """Fetch an application the viewer may see.

        Returns ``(application, is_applicant)``. Job seekers only see their
        own applications; employers only those for jobs in their company.
        Everyone else gets a 404 (existence is not disclosed).
        """
        application = await self.repository.get_by_id(application_id)
        if application is None:
            raise NotFoundException(detail="Application not found")

        if application.applicant_id == user.id:
            return application, True
        if self._user_manages_job(user, application):
            return application, False

        raise NotFoundException(detail="Application not found")

    async def list_my_applications(
        self,
        *,
        user: User,
        status: Optional[ApplicationStatus] = None,
        applied_after: Optional[datetime] = None,
        applied_before: Optional[datetime] = None,
        job_title: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Application], int]:
        self._validate_date_range(applied_after, applied_before)
        return await self.repository.list_for_applicant(
            applicant_id=user.id,
            status=status,
            applied_after=_ensure_aware(applied_after),
            applied_before=_ensure_aware(applied_before),
            job_title=job_title,
            offset=(page - 1) * limit,
            limit=limit,
        )

    async def list_company_applications(
        self,
        *,
        user: User,
        job_id: Optional[uuid.UUID] = None,
        status: Optional[ApplicationStatus] = None,
        applied_after: Optional[datetime] = None,
        applied_before: Optional[datetime] = None,
        sort_by: str = "applied_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[Sequence[Application], int]:
        company_id = await self._get_user_company_id(user)
        self._validate_date_range(applied_after, applied_before)
        return await self.repository.list_for_company(
            company_id=company_id,
            job_id=job_id,
            status=status,
            applied_after=_ensure_aware(applied_after),
            applied_before=_ensure_aware(applied_before),
            sort_by=sort_by,
            sort_order=sort_order,
            offset=(page - 1) * limit,
            limit=limit,
        )

    # ── Helpers ─────────────────────────────────────────────────────────

    async def _get_open_job(self, job_id: uuid.UUID) -> Job:
        result = await self.session.execute(
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.company).selectinload(Company.owner))
        )
        job = result.scalar_one_or_none()
        if job is None:
            raise NotFoundException(detail="Job not found")
        if job.status != JobStatus.published:
            raise BadRequestException(
                detail="This job is not open for applications"
            )
        deadline = _ensure_aware(job.application_deadline)
        if deadline is not None and deadline <= _utcnow():
            raise BadRequestException(
                detail="The application deadline for this job has passed"
            )
        return job

    @staticmethod
    def _user_manages_job(user: User, application: Application) -> bool:
        if user.role != UserRole.employer:
            return False
        company = application.job.company
        return (
            application.job.posted_by_id == user.id
            or (company is not None and company.owner_id == user.id)
        )

    async def _get_application_managed_by(
        self, user: User, application_id: uuid.UUID
    ) -> Application:
        application = await self.repository.get_by_id(application_id)
        if application is None:
            raise NotFoundException(detail="Application not found")
        if not self._user_manages_job(user, application):
            raise NotFoundException(detail="Application not found")
        return application

    async def _get_application_of_applicant(
        self, user: User, application_id: uuid.UUID
    ) -> Application:
        application = await self.repository.get_by_id(application_id)
        if application is None or application.applicant_id != user.id:
            raise NotFoundException(detail="Application not found")
        return application

    async def _get_user_company_id(self, user: User) -> uuid.UUID:
        if user.role != UserRole.employer:
            raise ForbiddenException(
                detail="Only employers can view company applications"
            )
        result = await self.session.execute(
            select(Company.id).where(Company.owner_id == user.id).limit(1)
        )
        company_id = result.scalar_one_or_none()
        if company_id is None:
            raise NotFoundException(detail="No company found for this employer")
        return company_id

    @staticmethod
    def _validate_date_range(
        applied_after: Optional[datetime], applied_before: Optional[datetime]
    ) -> None:
        if applied_after is not None and applied_before is not None:
            if _ensure_aware(applied_after) > _ensure_aware(applied_before):
                raise BadRequestException(
                    detail="applied_from must be before applied_to"
                )

    async def _refetch(self, application_id: uuid.UUID) -> Application:
        """Reload an application with all relationships eagerly loaded."""
        application = await self.repository.get_by_id(application_id)
        if application is None:  # pragma: no cover - row was just written
            raise NotFoundException(detail="Application not found")
        return application
