import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class EmploymentType(str, enum.Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"
    remote = "remote"


class ExperienceLevel(str, enum.Enum):
    entry = "entry"
    mid = "mid"
    senior = "senior"
    lead = "lead"


class JobStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"
    expired = "expired"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_company_id_status", "company_id", "status"),
        Index("ix_jobs_status_posted_date", "status", "posted_date"),
        Index("ix_jobs_category", "category"),
        # Week 5: full-text search + frequently filtered columns
        Index(
            "ix_jobs_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
        Index("ix_jobs_employment_type", "employment_type"),
        Index("ix_jobs_experience_level", "experience_level"),
        Index("ix_jobs_is_remote_status_posted_date", "is_remote", "status", "posted_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Core content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )
    responsibilities: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )

    # Employment details
    employment_type: Mapped[EmploymentType] = mapped_column(
        String(20), nullable=False
    )
    experience_level: Mapped[ExperienceLevel] = mapped_column(
        String(20), nullable=False, default=ExperienceLevel.entry
    )
    salary_min: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    salary_max: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="ETB")

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Full-text search (PostgreSQL generated column, kept in sync by the DB).
    # Weights: title='A', description='B', requirements='B', location='C'.
    search_vector = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(title, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(description, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(requirements::text, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(location, '')), 'C')",
            persisted=True,
        ),
        nullable=True,
    )

    # Relationships
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    posted_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Status & dates
    status: Mapped[JobStatus] = mapped_column(
        String(20), nullable=False, default=JobStatus.draft, index=True
    )
    application_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    posted_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    closing_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metadata / counters
    views_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    applications_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Optional extras
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    created_at: Mapped[datetime] = mapped_column(
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

    company: Mapped["Company"] = relationship(
        "Company", back_populates="jobs"
    )
    posted_by: Mapped["User"] = relationship("User", viewonly=True)

    @property
    def is_open(self) -> bool:
        return self.status == JobStatus.published

    def __repr__(self) -> str:
        return f"<Job {self.title} ({self.status})>"
