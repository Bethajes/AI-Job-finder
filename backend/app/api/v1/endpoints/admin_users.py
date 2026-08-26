"""Week 8: admin user-management endpoints."""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import compute_pagination
from app.dependencies.admin import require_admin
from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import (
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    UserAdminUpdate,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin/users", tags=["admin"])

MAX_PAGE_SIZE = 100


def _get_service(session: AsyncSession) -> AdminService:
    return AdminService(session)


def _request_context(request: Request) -> dict[str, Any]:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    search: Optional[str] = Query(None, max_length=200),
    role: Optional[str] = Query(None, pattern="^(job_seeker|employer|admin)$"),
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|last_login|email)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> AdminUserListResponse:
    """All platform users with search, filters, sorting and pagination."""
    service = _get_service(session)
    items, total = await service.list_users(
        search=search,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )
    filters = {
        key: value
        for key, value in {
            "search": search,
            "role": role,
            "is_active": is_active,
            "is_verified": is_verified,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }.items()
        if value is not None
    }
    return AdminUserListResponse(
        items=[AdminUserListItem.model_validate(u) for u in items],
        **compute_pagination(total=total, page=page, limit=limit),
        filters=filters,
    )


@router.get("/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    """Complete user profile incl. role-specific data and stats."""
    service = _get_service(session)
    user = await service.get_user_detail(user_id)
    detail = AdminUserDetail.model_validate(user)

    repo = AdminRepository(session)
    # str-enum comparison works whether the ORM returns enum or plain string.
    if user.role == "job_seeker":
        detail.application_stats = await repo.get_user_application_stats(user.id)
    elif user.role == "employer":
        detail.job_stats = await repo.get_employer_job_stats(user.id)
    return detail


@router.patch("/{user_id}", response_model=AdminUserDetail)
async def update_user(
    user_id: uuid.UUID,
    body: UserAdminUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    """Update role / activation / verification on a user account (audited)."""
    service = _get_service(session)
    ctx = _request_context(request)
    user = await service.update_user(
        admin=admin,
        user_id=user_id,
        data=body.model_dump(exclude_unset=True),
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )
    return AdminUserDetail.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
    hard: bool = Query(False, description="Hard-delete (cascade) instead of deactivating"),
) -> Any:
    """Soft-delete a user by default; `?hard=true` permanently deletes."""
    service = _get_service(session)
    ctx = _request_context(request)
    return await service.delete_user(
        admin=admin,
        user_id=user_id,
        hard=hard,
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )


@router.post("/{user_id}/verify", response_model=AdminUserDetail)
async def verify_user_email(
    user_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    """Manually verify a user's email address (audited override)."""
    service = _get_service(session)
    ctx = _request_context(request)
    user = await service.verify_user_email(
        admin=admin,
        user_id=user_id,
        ip_address=ctx["ip_address"],
        user_agent=ctx["user_agent"],
    )
    return AdminUserDetail.model_validate(user)
