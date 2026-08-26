import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import ApplicationSource, ApplicationStatus

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        # Hot query paths: employer pipelines filter by (job, status);
        # seekers filter their own list by status.
        Index("ix_applications_job_id_status", "job_id", "status"),
        Index("ix_applications_applicant_id_status", "applicant_id", "status"),
        Index("ix_applications_applied_at", "applied_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Relationships
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Application lifecycle
    status: Mapped[ApplicationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ApplicationStatus.APPLIED,
        index=True,
    )
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Documents: resume is required; extras (portfolios, certificates) are a
    # JSON array of {"name": str, "url": str} objects.
    resume_url: Mapped[str] = mapped_column(String(500), nullable=False)
    additional_documents: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )

    # Employer-only notes (never exposed to the applicant)
    employer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata / analytics
    source: Mapped[ApplicationSource] = mapped_column(
        String(20), nullable=False, default=ApplicationSource.WEB
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Timestamps
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    viewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    interview_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Counters denormalized for quick analytics (e.g. re-application rules)
    status_change_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    applicant: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Application {self.id} job={self.job_id} applicant={self.applicant_id} ({self.status})>"
