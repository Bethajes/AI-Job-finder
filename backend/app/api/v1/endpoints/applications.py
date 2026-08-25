"""Week 6: Job application endpoints (submission, listing, management)."""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    Query,
    Request,
    UploadFile,
    File,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.core.enums import ApplicationSource, ApplicationStatus
from app.core.pagination import compute_pagination
from app.models.user import User
from app.schemas.application import (
    ApplicationActionResponse,
    ApplicationCreate,
    ApplicationEmployerView,
    ApplicationSeekerView,
    ApplicationStatusUpdate,
    ApplicationWithdraw,
    CompanyApplicationsListResponse,
    MyApplicationsListResponse,
)
from app.services.application_service import ApplicationService
from app.services.notification_service import (
    send_application_confirmation,
    send_employer_new_application_notification,
    send_status_update_notification,
    send_withdrawal_confirmation,
    send_application_confirmation_push,
    send_status_update_push,
)

router = APIRouter(prefix="/applications", tags=["applications"])

MAX_PAGE_SIZE = 100


def _get_application_service(session: AsyncSession) -> ApplicationService:
    return ApplicationService(session)


def _client_ip(request: Request) -> Optional[str]:
    """Client IP for analytics; honors the first X-Forwarded-For hop."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ── Submission ──────────────────────────────────────────────────────


@router.post("", status_code=201)
async def apply_to_job(
    background_tasks: BackgroundTasks,
    request: Request,
    job_id: uuid.UUID = Form(...),
    cover_letter: Optional[str] = Form(None, max_length=5000),
    source: ApplicationSource = Form(ApplicationSource.WEB),
    resume: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Submit a job application (multipart/form-data).

    Requires a PDF/DOCX resume (max 5MB). Sends confirmation emails to the
    applicant and a notification to the employer as background tasks.
    """
    body = ApplicationCreate(
        job_id=job_id,
        cover_letter=cover_letter,
        # Form() yields an ApplicationSource member; the Literal-typed schema
        # field needs its plain string value (pydantic Literal + str-enum).
        source=source.value if isinstance(source, ApplicationSource) else source,
    )
    service = _get_application_service(session)
    application = await service.submit_application(
        user=current_user,
        job_id=body.job_id,
        resume_file=resume,
        cover_letter=body.cover_letter,
        source=ApplicationSource(body.source),
        ip_address=_client_ip(request),
    )

    job = application.job
    company = job.company
    applicant = application.applicant
    if company is not None and company.owner is not None:
        background_tasks.add_task(
            send_application_confirmation,
            applicant_email=applicant.email,
            applicant_first_name=applicant.first_name,
            job_title=job.title,
            company_name=company.name,
        )
        background_tasks.add_task(
            send_employer_new_application_notification,
            employer_email=company.owner.email,
            employer_first_name=company.owner.first_name,
            applicant_full_name=f"{applicant.first_name} {applicant.last_name}".strip(),
            job_title=job.title,
        )
        # Week 7: push notification to applicant
        background_tasks.add_task(
            send_application_confirmation_push,
            applicant_id=applicant.id,
            application_id=application.id,
            job_id=job.id,
            job_title=job.title,
            company_name=company.name,
        )

    data = ApplicationSeekerView.model_validate(application).model_dump(mode="json")
    data["message"] = "Application submitted successfully"
    return data


# ── Listings (keep above /{application_id} routes) ──────────────────


@router.get("/me", response_model=MyApplicationsListResponse)
async def list_my_applications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    status: Optional[ApplicationStatus] = None,
    applied_from: Optional[datetime] = None,
    applied_to: Optional[datetime] = None,
    job_title: Optional[str] = Query(None, max_length=200),
) -> MyApplicationsListResponse:
    """All applications of the authenticated job seeker (newest first)."""
    service = _get_application_service(session)
    items, total = await service.list_my_applications(
        user=current_user,
        status=status,
        applied_after=applied_from,
        applied_before=applied_to,
        job_title=job_title,
        page=page,
        limit=limit,
    )
    filters: dict[str, Any] = {
        key: value
        for key, value in {
            "status": status.value if status else None,
            "applied_from": applied_from.isoformat() if applied_from else None,
            "applied_to": applied_to.isoformat() if applied_to else None,
            "job_title": job_title,
        }.items()
        if value is not None
    }
    return MyApplicationsListResponse(
        items=[ApplicationSeekerView.model_validate(item) for item in items],
        **compute_pagination(total=total, page=page, limit=limit),
        filters=filters,
    )


@router.get("/company", response_model=CompanyApplicationsListResponse)
async def list_company_applications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    job_id: Optional[uuid.UUID] = None,
    status: Optional[ApplicationStatus] = None,
    applied_from: Optional[datetime] = None,
    applied_to: Optional[datetime] = None,
    sort_by: str = Query("applied_at", pattern="^(applied_at|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> CompanyApplicationsListResponse:
    """Applications to all jobs owned by the authenticated employer's company."""
    service = _get_application_service(session)
    items, total = await service.list_company_applications(
        user=current_user,
        job_id=job_id,
        status=status,
        applied_after=applied_from,
        applied_before=applied_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )
    filters: dict[str, Any] = {
        key: value
        for key, value in {
            "job_id": str(job_id) if job_id else None,
            "status": status.value if status else None,
            "applied_from": applied_from.isoformat() if applied_from else None,
            "applied_to": applied_to.isoformat() if applied_to else None,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }.items()
        if value is not None
    }
    return CompanyApplicationsListResponse(
        items=[ApplicationEmployerView.model_validate(item) for item in items],
        **compute_pagination(total=total, page=page, limit=limit),
        filters=filters,
    )


# ── Detail & management ─────────────────────────────────────────────


@router.get("/{application_id}")
async def get_application_details(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Full application details.

    Applicants never see `employer_notes`; employers see them for
    applications to their own jobs. Unauthorized viewers get a 404.
    """
    service = _get_application_service(session)
    application, is_applicant = await service.get_application_for_viewer(
        user=current_user, application_id=application_id
    )
    if is_applicant:
        return ApplicationSeekerView.model_validate(application).model_dump(mode="json")
    return ApplicationEmployerView.model_validate(application).model_dump(mode="json")


@router.patch("/{application_id}/status", response_model=ApplicationEmployerView)
async def update_application_status(
    application_id: uuid.UUID,
    body: ApplicationStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApplicationEmployerView:
    """Move an application through the hiring pipeline (employer only).

    Allowed transitions:
        applied → viewed → shortlisted → interviewed → offered → hired
    plus rejection from any active stage.
    """
    service = _get_application_service(session)
    application = await service.update_application_status(
        user=current_user,
        application_id=application_id,
        data=body.model_dump(exclude_unset=True),
    )

    job = application.job
    applicant = application.applicant
    background_tasks.add_task(
        send_status_update_notification,
        applicant_email=applicant.email,
        applicant_first_name=applicant.first_name,
        job_title=job.title,
        company_name=(
            job.company.name if job.company is not None else "the employer"
        ),
        new_status=ApplicationStatus(application.status),
    )
    # Week 7: push notification to applicant on status change
    background_tasks.add_task(
        send_status_update_push,
        applicant_id=applicant.id,
        application_id=application.id,
        job_id=job.id,
        job_title=job.title,
        company_name=job.company.name if job.company is not None else "the employer",
        new_status=ApplicationStatus(application.status).value,
    )

    return ApplicationEmployerView.model_validate(application)


@router.patch("/{application_id}/withdraw", response_model=ApplicationActionResponse)
async def withdraw_application(
    application_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    body: Optional[ApplicationWithdraw] = None,
) -> ApplicationActionResponse:
    """Withdraw an active application (applicant only).

    A withdrawn or rejected application allows re-applying later.
    """
    service = _get_application_service(session)
    application = await service.withdraw_application(
        user=current_user, application_id=application_id
    )

    job = application.job
    background_tasks.add_task(
        send_withdrawal_confirmation,
        applicant_email=current_user.email,
        applicant_first_name=current_user.first_name,
        job_title=job.title,
        company_name=(
            job.company.name if job.company is not None else "the employer"
        ),
    )

    return ApplicationActionResponse(
        id=application.id,
        status=application.status,
        detail="Application withdrawn",
    )
