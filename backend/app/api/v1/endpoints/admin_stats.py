"""Week 8: admin dashboard stats & reports endpoints (Redis-cached)."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.admin import require_admin
from app.models.user import User
from app.schemas.stats import (
    DashboardStatsResponse,
    JobPerformanceReportResponse,
    JobStatsResponse,
    UserActivityReportResponse,
    UserStatsResponse,
)
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_service(session: AsyncSession) -> AdminService:
    return AdminService(session)


@router.get("/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> DashboardStatsResponse:
    """Platform overview (users, jobs, applications, companies, activity)."""
    service = _get_service(session)
    stats = await service.get_dashboard_stats()
    return DashboardStatsResponse.model_validate(stats)


@router.get("/stats/users", response_model=UserStatsResponse)
async def user_stats(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UserStatsResponse:
    """User growth chart (last 30 days) and distribution breakdowns."""
    service = _get_service(session)
    stats = await service.get_user_stats()
    return UserStatsResponse.model_validate(stats)


@router.get("/stats/jobs", response_model=JobStatsResponse)
async def job_stats(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> JobStatsResponse:
    """Job posting trends, popular categories and application averages."""
    service = _get_service(session)
    stats = await service.get_job_stats()
    return JobStatsResponse.model_validate(stats)


@router.get("/reports/user-activity", response_model=UserActivityReportResponse)
async def user_activity_report(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> UserActivityReportResponse:
    """Engagement metrics: active users by window + most active applicants."""
    service = _get_service(session)
    report = await service.get_user_activity_report()
    return UserActivityReportResponse.model_validate(report)


@router.get("/reports/job-performance", response_model=JobPerformanceReportResponse)
async def job_performance_report(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> JobPerformanceReportResponse:
    """Top jobs by applications, time-to-fill and category/industry splits."""
    service = _get_service(session)
    report = await service.get_job_performance_report()
    return JobPerformanceReportResponse.model_validate(report)
