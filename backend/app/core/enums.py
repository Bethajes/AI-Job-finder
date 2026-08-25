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
