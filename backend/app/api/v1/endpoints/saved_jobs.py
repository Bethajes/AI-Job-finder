"""Week 7: Saved-jobs endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.core.pagination import compute_pagination
from app.models.user import User
from app.schemas.saved_job import (
    SavedJobActionResponse,
    SavedJobView,
    SavedJobsListResponse,
)
from app.services.saved_job_service import SavedJobService

router = APIRouter(prefix="/saved-jobs", tags=["saved-jobs"])

MAX_PAGE_SIZE = 100


def _get_service(session: AsyncSession) -> SavedJobService:
    return SavedJobService(session)


# ── List (keep above /{job_id} routes) ─────────────────────────────────


@router.get("/me", response_model=SavedJobsListResponse)
async def list_my_saved_jobs(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
) -> SavedJobsListResponse:
    """All saved jobs for the authenticated user (newest first)."""
    service = _get_service(session)
    items, total = await service.list_saved_jobs(
        user_id=current_user.id, page=page, limit=limit
    )
    return SavedJobsListResponse(
        items=[SavedJobView.model_validate(item) for item in items],
        **compute_pagination(total=total, page=page, limit=limit),
    )


# ── Save / Unsave ──────────────────────────────────────────────────────


@router.post("/{job_id}", status_code=201)
async def save_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SavedJobActionResponse:
    """Save a job for the authenticated user."""
    import uuid as _uuid

    service = _get_service(session)
    saved_job, is_new = await service.save_job(
        user_id=current_user.id,
        job_id=_uuid.UUID(job_id),
    )
    code = 201 if is_new else 200
    return SavedJobActionResponse(
        id=saved_job.id,
        job_id=saved_job.job_id,
        message="Job saved" if is_new else "Job was already saved",
    )


@router.delete("/{job_id}")
async def unsave_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SavedJobActionResponse:
    """Unsave a job (remove from saved list)."""
    import uuid as _uuid

    service = _get_service(session)
    removed = await service.unsave_job(
        user_id=current_user.id,
        job_id=_uuid.UUID(job_id),
    )
    return SavedJobActionResponse(
        job_id=_uuid.UUID(job_id),
        message="Job removed from saved list" if removed else "Job was not in saved list",
    )
