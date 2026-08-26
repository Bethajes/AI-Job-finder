"""Pydantic schemas for the Week 8 admin dashboard & management system."""

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

UserRoleLiteral = Literal["job_seeker", "employer", "admin"]
VerificationStatusLiteral = Literal["pending", "approved", "rejected"]
JobStatusLiteral = Literal["draft", "published", "closed", "expired"]

JobModerationActionLiteral = Literal[
    "approve", "reject", "flag", "unflag", "hide", "unhide"
]


# ── Request bodies ──────────────────────────────────────────────────


class UserAdminUpdate(BaseModel):
    """Fields an admin may change on another user."""

    role: Optional[UserRoleLiteral] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserAdminUpdate":
        if self.role is None and self.is_active is None and self.is_verified is None:
            raise ValueError("Provide at least one field to update")
        return self


class CompanyVerificationRequest(BaseModel):
    status: VerificationStatusLiteral
    admin_notes: Optional[str] = Field(None, max_length=2000)


class JobModerationRequest(BaseModel):
    action: JobModerationActionLiteral
    admin_notes: Optional[str] = Field(None, max_length=2000)


# ── User management responses ───────────────────────────────────────


class SeekerProfileBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = None
    skills: list[Any] = Field(default_factory=list)
    experience_years: Optional[int] = None
    city: Optional[str] = None


class OwnedCompanyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    is_verified: bool


class AdminUserListItem(BaseModel):
    """User row in the admin listing (no password hash ever leaves)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class AdminUserDetail(AdminUserListItem):
    """Complete user profile incl. role-specific data and stats."""

    job_seeker_profile: Optional[SeekerProfileBrief] = None
    companies: list[OwnedCompanyBrief] = Field(default_factory=list)
    application_stats: dict[str, Any] = Field(default_factory=dict)
    job_stats: dict[str, Any] = Field(default_factory=dict)


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool
    filters: dict[str, Any] = Field(default_factory=dict)


# ── Company management responses ────────────────────────────────────


class CompanyOwnerBrief(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str

    @model_validator(mode="before")
    @classmethod
    def build_full_name(cls, data: Any) -> Any:
        # Accept an ORM User and combine first/last names.
        if hasattr(data, "first_name") and not isinstance(data, dict):
            return {
                "id": data.id,
                "email": data.email,
                "full_name": f"{data.first_name} {data.last_name}".strip(),
            }
        return data


class AdminCompanyListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    industry: Optional[str] = None
    city: Optional[str] = None
    is_active: bool
    verification_status: Optional[str] = None
    is_verified: bool
    admin_notes: Optional[str] = None
    created_at: datetime


class AdminCompanyDetail(AdminCompanyListItem):
    owner: CompanyOwnerBrief
    description: Optional[str] = None
    job_count: int = 0
    total_applications: int = 0
    verified_at: Optional[datetime] = None


class AdminCompanyListResponse(BaseModel):
    items: list[AdminCompanyListItem]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool
    filters: dict[str, Any] = Field(default_factory=dict)


# ── Job moderation responses ────────────────────────────────────────


class AdminJobCompanyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class AdminJobListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: str
    employment_type: str
    location: Optional[str] = None
    category: Optional[str] = None
    company_id: uuid.UUID
    company: AdminJobCompanyBrief
    views_count: int
    applications_count: int
    is_hidden: bool
    is_flagged: bool
    flagged_at: Optional[datetime] = None
    posted_date: Optional[datetime] = None
    created_at: datetime


class AdminJobDetail(AdminJobListItem):
    description: str
    admin_notes: Optional[str] = None
    application_stats: dict[str, Any] = Field(default_factory=dict)


class AdminJobListResponse(BaseModel):
    items: list[AdminJobListItem]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool
    filters: dict[str, Any] = Field(default_factory=dict)


# ── Audit log responses ─────────────────────────────────────────────


class AdminLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    admin_id: Optional[uuid.UUID] = None
    admin_email: Optional[str] = None
    action_type: str
    resource_type: str
    resource_id: Optional[uuid.UUID] = None
    changes: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def flatten_admin(cls, data: Any) -> Any:
        # Accept the ORM row and pull admin_email off the relationship.
        if hasattr(data, "admin") and not isinstance(data, dict):
            admin_email = data.admin.email if data.admin is not None else None
            payload = {
                "id": data.id,
                "admin_id": data.admin_id,
                "admin_email": admin_email,
                "action_type": data.action_type,
                "resource_type": data.resource_type,
                "resource_id": data.resource_id,
                "changes": data.changes,
                "ip_address": data.ip_address,
                "user_agent": data.user_agent,
                "created_at": data.created_at,
            }
            return payload
        return data


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminLogEntry]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool
    filters: dict[str, Any] = Field(default_factory=dict)
