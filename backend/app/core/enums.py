"""Shared application-level enums (Week 6: job application flow)."""

import enum


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    VIEWED = "viewed"
    SHORTLISTED = "shortlisted"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationSource(str, enum.Enum):
    """Where an application originated from (analytics)."""

    WEB = "web"
    MOBILE = "mobile"
    API = "api"
    REFERRAL = "referral"


# Allowed employer-driven status transitions:
#   applied → viewed → shortlisted → interviewed → offered → hired
#   rejected is reachable from any active stage.
EMPLOYER_STATUS_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.APPLIED: {ApplicationStatus.VIEWED, ApplicationStatus.REJECTED},
    ApplicationStatus.VIEWED: {ApplicationStatus.SHORTLISTED, ApplicationStatus.REJECTED},
    ApplicationStatus.SHORTLISTED: {
        ApplicationStatus.INTERVIEWED,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.INTERVIEWED: {ApplicationStatus.OFFERED, ApplicationStatus.REJECTED},
    ApplicationStatus.OFFERED: {ApplicationStatus.HIRED, ApplicationStatus.REJECTED},
}

TERMINAL_STATUSES: frozenset[ApplicationStatus] = frozenset(
    {
        ApplicationStatus.HIRED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    }
)


# ── Week 8: admin dashboard & management ────────────────────────────────


class VerificationStatus(str, enum.Enum):
    """Company verification lifecycle (admin-driven)."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AdminActionType(str, enum.Enum):
    """Audit-trail action taxonomy for admin operations."""

    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_VERIFY = "user_verify"
    COMPANY_VERIFY = "company_verify"
    COMPANY_DELETE = "company_delete"
    JOB_MODERATE = "job_moderate"
    JOB_DELETE = "job_delete"


class AdminResourceType(str, enum.Enum):
    """Resource kinds an admin action can target."""

    USER = "user"
    COMPANY = "company"
    JOB = "job"
    APPLICATION = "application"
