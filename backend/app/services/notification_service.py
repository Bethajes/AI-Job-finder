"""Background notification tasks for the job application flow.

Module-level functions are safe to run via FastAPI's ``BackgroundTasks`` after
the response has been sent: they never raise, only log failures, so a broken
email provider or missing Firebase credentials can't turn an already-successful
write into a client error.

Week 7 additions: ``PushNotificationService`` for FCM push notifications
plus async background-task wrappers for each notification event.
"""

import asyncio
import logging
import re
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ApplicationStatus
from app.core.database import AsyncSessionLocal
from app.models.device_token import DeviceToken, _hash_token
from app.models.job import Job, JobStatus
from app.models.job_seeker import JobSeekerProfile
from app.models.user import User, UserRole, DEFAULT_NOTIFICATION_PREFERENCES
from app.repositories.notification_repository import DeviceTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.utils.email_templates import (
    application_confirmation_html,
    application_status_update_html,
    application_withdrawn_confirmation_html,
    new_application_employer_html,
)

logger = logging.getLogger(__name__)

email_service = EmailService()


# ── Email background tasks (Week 6, unchanged) ─────────────────────────


async def send_application_confirmation(
    *,
    applicant_email: str,
    applicant_first_name: str,
    job_title: str,
    company_name: str,
) -> None:
    """Confirm to the applicant that their application was received."""
    subject, html = application_confirmation_html(
        applicant_first_name, job_title, company_name
    )
    sent = await email_service.send_email(
        to=applicant_email, subject=subject, html=html
    )
    if not sent:
        logger.warning(
            "Application confirmation email failed applicant=%s job=%s",
            applicant_email,
            job_title,
        )


async def send_employer_new_application_notification(
    *,
    employer_email: str,
    employer_first_name: str,
    applicant_full_name: str,
    job_title: str,
) -> None:
    """Notify the employer that a new application arrived."""
    subject, html = new_application_employer_html(
        employer_first_name, applicant_full_name, job_title
    )
    sent = await email_service.send_email(
        to=employer_email, subject=subject, html=html
    )
    if not sent:
        logger.warning(
            "Employer new-application email failed employer=%s job=%s",
            employer_email,
            job_title,
        )


async def send_status_update_notification(
    *,
    applicant_email: str,
    applicant_first_name: str,
    job_title: str,
    company_name: str,
    new_status: ApplicationStatus,
) -> None:
    """Tell the applicant their application status changed."""
    subject, html = application_status_update_html(
        applicant_first_name, job_title, company_name, new_status.value
    )
    sent = await email_service.send_email(
        to=applicant_email, subject=subject, html=html
    )
    if not sent:
        logger.warning(
            "Status update email failed applicant=%s job=%s status=%s",
            applicant_email,
            job_title,
            new_status.value,
        )


async def send_withdrawal_confirmation(
    *,
    applicant_email: str,
    applicant_first_name: str,
    job_title: str,
    company_name: str,
) -> None:
    """Confirm to the applicant that they withdrew their application."""
    subject, html = application_withdrawn_confirmation_html(
        applicant_first_name, job_title, company_name
    )
    sent = await email_service.send_email(
        to=applicant_email, subject=subject, html=html
    )
    if not sent:
        logger.warning(
            "Withdrawal confirmation email failed applicant=%s job=%s",
            applicant_email,
            job_title,
        )


# ── Push notification service (Week 7) ─────────────────────────────────


class PushNotificationService:
    """Stateful service that wraps device-token and notification-pref logic
    around the FCM core in ``app.core.fcm``.

    All public methods are **async** and accept a live ``AsyncSession``.
    Callers (background-task wrappers) create their own session via
    ``AsyncSessionLocal`` to avoid lifetime issues with DI sessions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.device_repo = DeviceTokenRepository(session)
        self.user_repo = UserRepository(session)

    # ── Core methods (per spec) ─────────────────────────────────────────

    async def send_push_notification(
        self,
        user_id: uuid.UUID,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a push notification to all of *user_id*'s active devices.

        Checks the user's notification preferences before sending and
        cleans up any tokens that FCM reports as permanently invalid.
        """
        from app.core import fcm

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return {"sent": 0, "failed": 0, "invalid_tokens": []}

        prefs = _get_prefs(user)
        if not prefs.get("in_app", True):
            return {"sent": 0, "failed": 0, "invalid_tokens": []}

        tokens = await self.device_repo.get_active_tokens_for_user(user_id)
        if not tokens:
            return {"sent": 0, "failed": 0, "invalid_tokens": []}

        result = await fcm.send_push_notification(
            list(tokens), title, body, data
        )

        # Clean up invalid tokens in the background.
        if result.get("invalid_tokens"):
            hashes = [_hash_token(t) for t in result["invalid_tokens"]]
            await self.device_repo.deactivate_tokens(hashes)
            logger.info(
                "Deactivated %d invalid FCM tokens for user %s",
                len(hashes),
                user_id,
            )

        return result

    async def save_device_token(
        self, user_id: uuid.UUID, token: str, device_type: str
    ) -> DeviceToken:
        return await self.device_repo.upsert_token(user_id, token, device_type)

    async def remove_device_token(self, user_id: uuid.UUID, token: str) -> bool:
        return await self.device_repo.deactivate_by_token(token)

    # ── Event-specific helpers ──────────────────────────────────────────

    async def notify_application_confirmation(
        self,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        job_title: str,
        company_name: str,
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return
        prefs = _get_prefs(user)
        if not prefs.get("application_updates", True):
            return

        title = "Application Submitted"
        body = f"You applied for {job_title} at {company_name}"
        data = {
            "type": "application_confirmation",
            "application_id": str(application_id),
        }
        await self.send_push_notification(user_id, title, body, data)

    async def notify_status_change(
        self,
        user_id: uuid.UUID,
        application_id: uuid.UUID,
        job_title: str,
        company_name: str,
        new_status: str,
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return
        prefs = _get_prefs(user)
        if not prefs.get("application_updates", True):
            return

        title = "Application Status Update"
        body = f"Your application for {job_title} is now {new_status}"
        data = {
            "type": "status_change",
            "application_id": str(application_id),
            "new_status": new_status,
        }
        await self.send_push_notification(user_id, title, body, data)

    async def notify_new_job(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        job_title: str,
        company_name: str,
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return
        prefs = _get_prefs(user)
        if not prefs.get("new_jobs", True):
            return

        title = "New Job Opportunity"
        body = f"{job_title} at {company_name}"
        data = {
            "type": "new_job",
            "job_id": str(job_id),
        }
        await self.send_push_notification(user_id, title, body, data)


def _get_prefs(user: User) -> dict[str, Any]:
    """Merge stored preferences with defaults."""
    stored = user.notification_preferences or {}
    merged: dict[str, Any] = dict(DEFAULT_NOTIFICATION_PREFERENCES)
    merged.update(stored)
    return merged


# ── Background-task wrappers (own sessions, never raise) ────────────────
#
# These are the functions added via ``background_tasks.add_task(...)`` in
# endpoint handlers.  Each opens its own DB session so they work correctly
# even after the request-scoped session has been closed.


async def send_application_confirmation_push(
    *,
    applicant_id: uuid.UUID,
    application_id: uuid.UUID,
    job_id: uuid.UUID,
    job_title: str,
    company_name: str,
) -> None:
    """Push notification when an application is submitted."""
    try:
        async with AsyncSessionLocal() as session:
            svc = PushNotificationService(session)
            await svc.notify_application_confirmation(
                user_id=applicant_id,
                application_id=application_id,
                job_title=job_title,
                company_name=company_name,
            )
    except Exception:
        logger.exception(
            "Push notification (application confirmation) failed user=%s",
            applicant_id,
        )


async def send_status_update_push(
    *,
    applicant_id: uuid.UUID,
    application_id: uuid.UUID,
    job_id: uuid.UUID,
    job_title: str,
    company_name: str,
    new_status: str,
) -> None:
    """Push notification when application status changes."""
    try:
        async with AsyncSessionLocal() as session:
            svc = PushNotificationService(session)
            await svc.notify_status_change(
                user_id=applicant_id,
                application_id=application_id,
                job_title=job_title,
                company_name=company_name,
                new_status=new_status,
            )
    except Exception:
        logger.exception(
            "Push notification (status update) failed user=%s",
            applicant_id,
        )


async def send_new_job_alerts_push(
    *,
    job_id: uuid.UUID,
) -> None:
    """Notify matching job seekers when a new job is published."""
    try:
        async with AsyncSessionLocal() as session:
            svc = PushNotificationService(session)

            # Load the new job
            result = await session.execute(
                select(Job)
                .where(Job.id == job_id)
                .options(selectinload(Job.company))
            )
            job = result.scalar_one_or_none()
            if job is None:
                return

            company_name = job.company.name if job.company else "an employer"
            keywords = _extract_keywords(job.title, job.category or "", job.location or "")
            if not keywords:
                return

            # Find matching seekers
            matching_user_ids = await _find_matching_seeker_ids(session, keywords, job.location)

            for uid in matching_user_ids:
                try:
                    await svc.notify_new_job(
                        user_id=uid,
                        job_id=job_id,
                        job_title=job.title,
                        company_name=company_name,
                    )
                except Exception:
                    logger.exception("Push notification (new job alert) failed user=%s", uid)

    except Exception:
        logger.exception("New job alert task failed job=%s", job_id)


def _extract_keywords(*texts: str) -> list[str]:
    """Pull meaningful words (length > 2) from free-text fields."""
    words: list[str] = []
    for text in texts:
        if not text:
            continue
        words.extend(
            w.lower()
            for w in re.split(r"\W+", text)
            if len(w) > 2
        )
    return list(dict.fromkeys(words))[:20]


async def _find_matching_seeker_ids(
    session: AsyncSession,
    keywords: list[str],
    location: str | None,
) -> list[uuid.UUID]:
    """Return user IDs of job seekers whose skills or city match the job."""
    from sqlalchemy import or_

    stmt = (
        select(JobSeekerProfile.user_id)
        .join(User, User.id == JobSeekerProfile.user_id)
        .where(
            User.role == UserRole.job_seeker,
            User.is_active.is_(True),
        )
    )

    conditions = []
    if location:
        conditions.append(
            func.lower(JobSeekerProfile.city) == location.lower()  # type: ignore[union-attr]
        )

    if conditions:
        stmt = stmt.where(or_(*conditions))

    # Cap at 500 recipients to respect FCM rate limits
    stmt = stmt.limit(500)

    result = await session.execute(stmt)
    return list(result.scalars().all())
