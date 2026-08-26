"""Week 8: admin audit-log viewing endpoint."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import compute_pagination
from app.core.rate_limit import rate_limit
from app.dependencies.admin import require_admin
from app.models.user import User
from app.schemas.admin import AdminAuditLogListResponse, AdminLogEntry
from app.services.audit_service import AuditService

router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["admin"],
    dependencies=[rate_limit("admin")],
)

MAX_PAGE_SIZE = 100


@router.get("", response_model=AdminAuditLogListResponse)
async def list_audit_logs(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    admin_id: Optional[uuid.UUID] = None,
    action_type: Optional[str] = Query(
        None,
        pattern="^(user_update|user_delete|user_verify|company_verify|company_delete|job_moderate|job_delete)$",
    ),
    resource_type: Optional[str] = Query(None, pattern="^(user|company|job|application)$"),
    resource_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> AdminAuditLogListResponse:
    """Full audit trail with filters (acting admin, action, resource, dates)."""
    service = AuditService(session)
    items, total = await service.list_logs(
        admin_id=admin_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    filters = {
        key: value
        for key, value in {
            "admin_id": str(admin_id) if admin_id else None,
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }.items()
        if value is not None
    }
    return AdminAuditLogListResponse(
        items=[AdminLogEntry.model_validate(entry) for entry in items],
        **compute_pagination(total=total, page=page, limit=limit),
        filters=filters,
    )
