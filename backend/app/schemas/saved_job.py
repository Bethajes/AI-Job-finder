"""Pydantic schemas for the saved-jobs feature (Week 7)."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Job brief embedded in saved-job responses ───────────────────────────


class SavedJobJobBrief(BaseModel):
    """Job card embedded in saved-job responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    employment_type: str
    location: Optional[str] = None
    is_remote: bool = False
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "ETB"
    company_name: str = ""

    @model_validator(mode="before")
    @classmethod
    def flatten_job(cls, data: Any) -> Any:
        if hasattr(data, "company"):
            return {
                "id": data.id,
                "title": data.title,
                "employment_type": data.employment_type,
                "location": data.location,
                "is_remote": data.is_remote,
                "salary_min": float(data.salary_min) if data.salary_min else None,
                "salary_max": float(data.salary_max) if data.salary_max else None,
                "currency": data.currency,
                "company_name": data.company.name if data.company else "",
            }
        return data


# ── Response models ─────────────────────────────────────────────────────


class SavedJobView(BaseModel):
    """Single saved-job entry with full job details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    is_active: bool
    created_at: datetime
    job: SavedJobJobBrief


class SavedJobsListResponse(BaseModel):
    """Paginated list of saved jobs."""

    items: list[SavedJobView]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool


class SavedJobActionResponse(BaseModel):
    """Returned on save / unsave."""

    id: Optional[uuid.UUID] = None
    job_id: uuid.UUID
    message: str
