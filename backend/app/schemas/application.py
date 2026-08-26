"""Pydantic schemas for the job application flow (Week 6)."""

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.core.enums import ApplicationStatus

ApplicationStatusLiteral = Literal[
    "applied",
    "viewed",
    "shortlisted",
    "interviewed",
    "offered",
    "hired",
    "rejected",
    "withdrawn",
]

ApplicationSourceLiteral = Literal["web", "mobile", "api", "referral"]

SortByLiteral = Literal["applied_at", "status"]
SortOrderLiteral = Literal["asc", "desc"]


def coerce_status(value: Any) -> Any:
    """Accept an ``ApplicationStatus`` member wherever a status literal goes.

    ORM instances can carry the enum in memory after updates; pydantic's
    Literal validator rejects str-enum members, so unwrap them early.
    """
    if isinstance(value, ApplicationStatus):
        return value.value
    return value


# ── Create (multipart/form-data body; resume arrives as UploadFile) ─


class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    cover_letter: Optional[str] = Field(None, max_length=5000)
    source: ApplicationSourceLiteral = "web"


# ── Update ──────────────────────────────────────────────────────────


class ApplicationStatusUpdate(BaseModel):
    """Employer-driven status change (+ optional notes / interview date)."""

    status: ApplicationStatusLiteral
    employer_notes: Optional[str] = Field(None, max_length=5000)
    interview_date: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_interview_date(self) -> "ApplicationStatusUpdate":
        if self.interview_date is not None and self.status != "interviewed":
            raise ValueError(
                "interview_date can only be set when moving to 'interviewed'"
            )
        return self


class ApplicationWithdraw(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000)


# ── Nested views ────────────────────────────────────────────────────


class ApplicationJobBrief(BaseModel):
    """Job card embedded in application responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    employment_type: str
    location: Optional[str] = None
    is_remote: bool = False
    company_name: str = ""

    @model_validator(mode="before")
    @classmethod
    def flatten_company(cls, data: Any) -> Any:
        # Accept an ORM Job and pull company_name off the relationship.
        if hasattr(data, "company"):
            return {
                "id": data.id,
                "title": data.title,
                "employment_type": data.employment_type,
                "location": data.location,
                "is_remote": data.is_remote,
                "company_name": data.company.name if data.company else "",
            }
        return data


class ApplicantSummary(BaseModel):
    """Applicant identity + profile summary for employer views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    headline: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def extract_profile(cls, data: Any) -> Any:
        # Accept an ORM User and pull the summary off job_seeker_profile.
        if hasattr(data, "job_seeker_profile"):
            profile = data.job_seeker_profile
            return {
                "id": data.id,
                "full_name": f"{data.first_name} {data.last_name}".strip(),
                "email": data.email,
                "headline": getattr(profile, "title", None) if profile else None,
                "location": getattr(profile, "city", None) if profile else None,
                "experience_years": (
                    getattr(profile, "experience_years", None) if profile else None
                ),
            }
        return data


# ── Response base ───────────────────────────────────────────────────


class _ApplicationFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    applicant_id: uuid.UUID
    status: ApplicationStatusLiteral
    cover_letter: Optional[str] = None
    resume_url: str
    additional_documents: list[Any] = Field(default_factory=list)
    source: ApplicationSourceLiteral = "web"
    applied_at: datetime
    updated_at: datetime
    viewed_at: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    job: ApplicationJobBrief
    applicant: ApplicantSummary

    _coerce_status = field_validator("status", mode="before")(coerce_status)


class ApplicationEmployerView(_ApplicationFields):
    """Full application view for employers (includes private notes)."""

    employer_notes: Optional[str] = None
    ip_address: Optional[str] = None


class ApplicationSeekerView(_ApplicationFields):
    """Applicant-facing view: employer notes and analytics are hidden."""

    pass


# ── Paginated lists ─────────────────────────────────────────────────


class CompanyApplicationsListResponse(BaseModel):
    """GET /applications/company — employer pipeline."""

    items: list[ApplicationEmployerView]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool
    filters: dict[str, Any] = Field(default_factory=dict)


class MyApplicationsListResponse(BaseModel):
    """GET /applications/me — job seeker history."""

    items: list[ApplicationSeekerView]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool
    filters: dict[str, Any] = Field(default_factory=dict)


# ── Misc ────────────────────────────────────────────────────────────


class ApplicationActionResponse(BaseModel):
    id: uuid.UUID
    status: ApplicationStatusLiteral
    detail: str

    _coerce_status = field_validator("status", mode="before")(coerce_status)
