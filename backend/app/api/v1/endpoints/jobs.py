import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_optional_current_user
from app.core.database import get_db
from app.dependencies.company import require_employer
from app.models.job import JobStatus
from app.models.user import User
from app.schemas.job import (
    JobActionResponse,
    JobCreate,
    JobListResponse,
    JobResponse,
    JobUpdate,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])

MAX_PAGE_SIZE = 100


def _get_job_service(session: AsyncSession) -> JobService:
    return JobService(session)


def _to_list_response(
    jobs, total: int, page: int, page_size: int
) -> JobListResponse:
    total_pages = max(1, -(-total // page_size))
    return JobListResponse(
        items=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ── Public listing (keep above /{job_id} routes) ────────────────────


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    company_id: Optional[uuid.UUID] = None,
    status: Optional[JobStatus] = None,
    employment_type: Optional[str] = Query(None, pattern="^(full-time|part-time|contract|internship|remote)$"),
    experience_level: Optional[str] = Query(None, pattern="^(entry|mid|senior|lead)$"),
    location: Optional[str] = None,
    category: Optional[str] = None,
    is_remote: Optional[bool] = None,
    search: Optional[str] = Query(None, max_length=200),
    viewer: Optional[User] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """Public job board listing with filters. Owners may filter private statuses."""
    service = _get_job_service(session)
    jobs, total = await service.list_public_jobs(
        viewer=viewer,
        page=page,
        page_size=page_size,
        company_id=company_id,
        status=status,
        employment_type=employment_type,
        experience_level=experience_level,
        location=location,
        category=category,
        is_remote=is_remote,
        search=search,
    )
    return _to_list_response(jobs, total, page, page_size)


# ── Employer actions ────────────────────────────────────────────────


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    body: JobCreate,
    current_user: User = Depends(require_employer),
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    service = _get_job_service(session)
    job = await service.create_job(user=current_user, data=body.model_dump())
    return JobResponse.model_validate(job)


# ── Item routes ─────────────────────────────────────────────────────


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_details(
    job_id: uuid.UUID,
    viewer: Optional[User] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Public job details; drafts and closed jobs are visible to their owner only."""
    service = _get_job_service(session)
    job = await service.get_job_detail(job_id, viewer=viewer)
    return JobResponse.model_validate(job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: uuid.UUID,
    body: JobUpdate,
    current_user: User = Depends(require_employer),
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    service = _get_job_service(session)
    data = body.model_dump(exclude_unset=True)
    job = await service.update_job(user=current_user, job_id=job_id, data=data)
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", response_model=JobActionResponse)
async def delete_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_employer),
    session: AsyncSession = Depends(get_db),
) -> JobActionResponse:
    """Soft delete: the job is closed (kept for record keeping/applications)."""
    service = _get_job_service(session)
    job = await service.delete_job(user=current_user, job_id=job_id)
    return JobActionResponse(
        id=job.id,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        detail="Job deleted (soft delete); status set to closed",
    )


@router.patch("/{job_id}/close", response_model=JobResponse)
async def close_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_employer),
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    service = _get_job_service(session)
    job = await service.close_job(user=current_user, job_id=job_id)
    return JobResponse.model_validate(job)


@router.patch("/{job_id}/publish", response_model=JobResponse)
async def publish_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_employer),
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    service = _get_job_service(session)
    job = await service.publish_job(user=current_user, job_id=job_id)
    return JobResponse.model_validate(job)
