"""Week 8: admin job moderation endpoints."""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import compute_pagination
from app.core.rate_limit import rate_limit
from app.dependencies.admin import require_admin
from app.models.job import JobStatus
from app.models.user import User
from app.schemas.admin import (
    AdminJobDetail,
    AdminJobListItem,
    AdminJobListResponse,
    JobModerationRequest,
)
from app.services.admin_service import AdminService

router = APIRouter(
    prefix="/admin/jobs",
    tags=["admin"],
    dependencies=[rate_limit("admin")],
)

MAX_PAGE_SIZE = 100


def _get_service(session: AsyncSession) -> AdminService:
    return AdminService(session)


def _request_context(request: Request) -> dict[str, Any]:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get("", response_model=AdminJobListResponse)
async def list_jobs(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    status: Optional[JobStatus] = None,
    company_id: Optional[uuid.UUID] = None,
    flagged_only: bool = False,
    hidden_only: bool = False,
    search: Optional[str] = Query(None, max_length=200),
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
) -> AdminJobListResponse:
    """All jobs with moderation filters (status, flagged, hidden, dates)."""
    service = _get_service(session)
    items, total = await service.list_jobs(
        status=status,
        company_id=company_id,
        flagged_only=flagged_only,
        hidden_only=hidden_only,
        search=search,
        created_after=created_from,
        created_before=created_to,
        page=page,
        limit=limit,
    )
    filters = {
        key: value
        for key, value in {
            "status": status.value if status else None,
            "company_id": str(company_id) if company_id else None,
            "flagged_only": flagged_only or None,
            "hidden_only": hidden_only or None,
            "search": search,
            "created_from": created_from.isoformat() if created_from else None,
            "created_to": created_to.isoformat() if created_to else None,
        }.items()
        if value is not None
    }
    return AdminJobListResponse(
        items=[AdminJobListItem.model_validate(j) for j in items],
        **compute_pagination(total=total, page=page, limit=limit),
        filters=filters,
    )


@router.get("/{job_id}", response_model=AdminJobDetail)
async def get_job_detail(
    job_id: uuid.UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminJobDetail:
    """Full job details incl. application stats and flag history fields."""
    service = _get_service(session)
    job = await service.get_job_detail(job_id)
    return AdminJobDetail.model_validate(job)


@router.patch("/{job_id}/moderate", response_model=AdminJobDetail)
async def moderate_job(
    job_id: uuid.UUID,
    body: JobModerationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminJobDetail:
    """Moderate a posting: approve / reject / flag / unflag / hide / unhide."""
    service = _get_service(session)
    ctx = _request_context(request)
    job = await service.moderate_job(
        admin=admin,
        job_id=job_id,
        action=body.action,
        admin_notes=body.admin_notes,
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )
    return AdminJobDetail.model_validate(job)


@router.delete("/{job_id}")
async def delete_job(
    job_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Remove an inappropriate job permanently (audited)."""
    service = _get_service(session)
    ctx = _request_context(request)
    return await service.delete_job(
        admin=admin,
        job_id=job_id,
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )
