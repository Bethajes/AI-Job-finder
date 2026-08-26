"""Pydantic schemas for admin dashboard stats and reports (Week 8)."""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """Platform overview: GET /admin/stats."""

    total_users: int
    users_by_role: dict[str, int]
    total_jobs: int
    jobs_by_status: dict[str, int]
    total_applications: int
    applications_by_status: dict[str, int]
    total_companies: int
    companies_by_verification: dict[str, int]
    new_users_7d: int
    new_users_30d: int
    new_jobs_7d: int
    new_jobs_30d: int
    active_users_24h: int
    active_users_7d: int
    generated_at: datetime


class GrowthPoint(BaseModel):
    date: date
    count: int


class UserStatsResponse(BaseModel):
    """User growth + distribution: GET /admin/stats/users."""

    growth_daily: list[GrowthPoint]
    distribution_by_role: dict[str, int]
    distribution_by_verification: dict[str, int]


class JobStatsResponse(BaseModel):
    """Job posting trends: GET /admin/stats/jobs."""

    posting_trend_daily: list[GrowthPoint]
    popular_categories: list[dict[str, Any]]
    jobs_by_employment_type: dict[str, int]
    average_applications_per_job: float


class MostActiveUser(BaseModel):
    user_id: str
    full_name: str
    email: str
    activity_count: int


class UserActivityReportResponse(BaseModel):
    """Engagement metrics: GET /admin/reports/user-activity."""

    active_users_daily: int
    active_users_weekly: int
    active_users_monthly: int
    applications_last_24h: int
    applications_last_7d: int
    most_active_users: list[MostActiveUser] = Field(default_factory=list)
    note: str = "Session duration is not tracked; engagement is measured by applications and logins."


class TopJob(BaseModel):
    job_id: str
    title: str
    company_name: Optional[str] = None
    applications_count: int


class JobPerformanceReportResponse(BaseModel):
    """Performance metrics: GET /admin/reports/job-performance."""

    top_jobs_by_applications: list[TopJob]
    average_applications_per_job: float
    average_days_to_fill: float | None = None
    jobs_by_industry: dict[str, int]
    jobs_by_employment_type: dict[str, int]
