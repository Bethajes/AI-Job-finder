"""Week 8: admin company approval & management endpoints."""

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import VerificationStatus
from app.core.pagination import compute_pagination
from app.core.rate_limit import rate_limit
from app.dependencies.admin import require_admin
from app.models.user import User
from app.schemas.admin import (
    AdminCompanyDetail,
    AdminCompanyListItem,
    AdminCompanyListResponse,
    CompanyVerificationRequest,
)
from app.services.admin_service import AdminService
from app.services.notification_service import send_company_verification_email

router = APIRouter(
    prefix="/admin/companies",
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


@router.get("", response_model=AdminCompanyListResponse)
async def list_companies(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    search: Optional[str] = Query(None, max_length=200),
    verification_status: Optional[VerificationStatus] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
) -> AdminCompanyListResponse:
    """All companies with verification / search / date filters."""
    service = _get_service(session)
    items, total = await service.list_companies(
        search=search,
        verification_status=verification_status,
        created_after=created_from,
        created_before=created_to,
        page=page,
        limit=limit,
    )
    filters = {
        key: value
        for key, value in {
            "search": search,
            "verification_status": (
                verification_status.value if verification_status else None
            ),
            "created_from": created_from.isoformat() if created_from else None,
            "created_to": created_to.isoformat() if created_to else None,
        }.items()
        if value is not None
    }
    return AdminCompanyListResponse(
        items=[AdminCompanyListItem.model_validate(c) for c in items],
        **compute_pagination(total=total, page=page, limit=limit),
        filters=filters,
    )


@router.get("/{company_id}", response_model=AdminCompanyDetail)
async def get_company_detail(
    company_id: uuid.UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminCompanyDetail:
    """Company details with owner, job count and application stats."""
    service = _get_service(session)
    company = await service.get_company_detail(company_id)
    return AdminCompanyDetail.model_validate(company)


@router.patch("/{company_id}/verify", response_model=AdminCompanyDetail)
async def verify_company(
    company_id: uuid.UUID,
    body: CompanyVerificationRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminCompanyDetail:
    """Approve / reject / reset company verification (audited).

    The company owner is emailed the outcome as a background task.
    """
    service = _get_service(session)
    ctx = _request_context(request)
    company = await service.verify_company(
        admin=admin,
        company_id=company_id,
        status=body.status,
        admin_notes=body.admin_notes,
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )

    owner = company.owner
    if owner is not None:
        background_tasks.add_task(
            send_company_verification_email,
            owner_email=owner.email,
            owner_first_name=owner.first_name,
            company_name=company.name,
            status=body.status,
            admin_notes=body.admin_notes,
        )

    return AdminCompanyDetail.model_validate(company)


@router.delete("/{company_id}")
async def delete_company(
    company_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
    hard: bool = Query(False, description="Cascade-delete instead of suspending"),
) -> Any:
    """Suspend a company by default; `?hard=true` cascades jobs and data."""
    service = _get_service(session)
    ctx = _request_context(request)
    return await service.delete_company(
        admin=admin,
        company_id=company_id,
        hard=hard,
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )
