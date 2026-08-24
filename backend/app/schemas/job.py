import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

EmploymentTypeLiteral = Literal[
    "full-time", "part-time", "contract", "internship", "remote"
]
ExperienceLevelLiteral = Literal["entry", "mid", "senior", "lead"]
JobStatusLiteral = Literal["draft", "published", "closed", "expired"]


def _validate_deadline_is_future(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return value
    aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if aware <= datetime.now(timezone.utc):
        raise ValueError("application_deadline must be in the future")
    return value


def _clean_string_list(values: list[str]) -> list[str]:
    return [item.strip() for item in values if item and item.strip()]


# ── Create ──────────────────────────────────────────────────────────


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10)
    requirements: list[str] = Field(default_factory=list, max_length=50)
    responsibilities: list[str] = Field(default_factory=list, max_length=50)

    company_id: uuid.UUID
    employment_type: EmploymentTypeLiteral
    experience_level: ExperienceLevelLiteral = "entry"

    salary_min: Optional[Decimal] = Field(None, ge=0, le=999_999_999_999)
    salary_max: Optional[Decimal] = Field(None, ge=0, le=999_999_999_999)
    currency: str = Field("ETB", min_length=3, max_length=3)

    location: Optional[str] = Field(None, max_length=255)
    is_remote: bool = False

    application_deadline: Optional[datetime] = None

    is_featured: bool = False
    category: Optional[str] = Field(None, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("requirements", "responsibilities", "tags")
    @classmethod
    def strip_items(cls, v: list[str]) -> list[str]:
        return _clean_string_list(v)

    @field_validator("application_deadline")
    @classmethod
    def deadline_must_be_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        return _validate_deadline_is_future(v)

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobCreate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must be less than or equal to salary_max")
        return self


# ── Update (PATCH semantics: all optional) ──────────────────────────


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    requirements: Optional[list[str]] = Field(None, max_length=50)
    responsibilities: Optional[list[str]] = Field(None, max_length=50)

    employment_type: Optional[EmploymentTypeLiteral] = None
    experience_level: Optional[ExperienceLevelLiteral] = None

    salary_min: Optional[Decimal] = Field(None, ge=0, le=999_999_999_999)
    salary_max: Optional[Decimal] = Field(None, ge=0, le=999_999_999_999)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

    location: Optional[str] = Field(None, max_length=255)
    is_remote: Optional[bool] = None

    application_deadline: Optional[datetime] = None

    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = Field(None, max_length=30)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v else v

    @field_validator("requirements", "responsibilities", "tags")
    @classmethod
    def strip_items(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        return _clean_string_list(v) if v is not None else None

    @field_validator("application_deadline")
    @classmethod
    def deadline_must_be_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        return _validate_deadline_is_future(v)

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobUpdate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must be less than or equal to salary_max")
        return self


# ── Responses ───────────────────────────────────────────────────────


class CompanyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    logo_url: Optional[str] = None
    city: Optional[str] = None
    is_verified: bool


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    requirements: list[str]
    responsibilities: list[str]

    employment_type: EmploymentTypeLiteral
    experience_level: ExperienceLevelLiteral
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    currency: str

    location: Optional[str] = None
    is_remote: bool

    company_id: uuid.UUID
    posted_by_id: uuid.UUID
    company: CompanyBrief

    status: JobStatusLiteral
    application_deadline: Optional[datetime] = None
    posted_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None

    views_count: int
    applications_count: int

    is_featured: bool
    category: Optional[str] = None
    tags: list[str]

    created_at: datetime
    updated_at: datetime

    @field_serializer("salary_min", "salary_max")
    def serialize_salary(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobActionResponse(BaseModel):
    id: uuid.UUID
    status: JobStatusLiteral
    detail: str


# ── Week 5: Search / filtering / sorting ────────────────────────────

SortByLiteral = Literal["relevance", "posted_date", "salary_max", "salary_min"]
SortOrderLiteral = Literal["asc", "desc"]


class JobSearchFilters(BaseModel):
    """Validated search + filter parameters for GET /jobs/search."""

    q: Optional[str] = Field(None, max_length=200)
    employment_type: Optional[EmploymentTypeLiteral] = None
    experience_level: Optional[ExperienceLevelLiteral] = None
    salary_min: Optional[Decimal] = Field(None, ge=0, le=999_999_999_999)
    salary_max: Optional[Decimal] = Field(None, ge=0, le=999_999_999_999)
    location: Optional[str] = Field(None, max_length=255)
    is_remote: Optional[bool] = None
    days_ago: Optional[int] = Field(None, ge=1, le=365)
    company_id: Optional[uuid.UUID] = None
    sort_by: SortByLiteral = "relevance"
    sort_order: SortOrderLiteral = "desc"

    @field_validator("q")
    @classmethod
    def strip_query(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobSearchFilters":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must be less than or equal to salary_max")
        return self


class JobSearchItem(BaseModel):
    """Slim job card used in search results."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    employment_type: EmploymentTypeLiteral
    experience_level: ExperienceLevelLiteral
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    currency: str
    location: Optional[str] = None
    is_remote: bool
    company_id: uuid.UUID
    company: CompanyBrief
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    category: Optional[str] = None
    tags: list[str]
    views_count: int
    relevance_score: Optional[float] = None

    @field_serializer("salary_min", "salary_max", "relevance_score")
    def serialize_floats(self, value: Optional[Decimal]) -> Optional[float]:
        return float(value) if value is not None else None


class JobSearchResponse(BaseModel):
    items: list[JobSearchItem]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool


# ── Week 5: Enhanced job detail ─────────────────────────────────────


class JobDetailResponse(JobResponse):
    """Full job view with company info and related openings."""

    related_jobs: list["JobSearchItem"] = Field(default_factory=list)


JobSearchItem.model_rebuild()
JobDetailResponse.model_rebuild()