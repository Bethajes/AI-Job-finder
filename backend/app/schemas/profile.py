import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProfileCompletenessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    completeness: int = Field(..., ge=0, le=100, description="Profile completeness percentage")
    missing_fields: list[str] = Field(..., description="List of field names still missing")


# ── Job Seeker Profile ──────────────────────────────────────────────


class JobSeekerProfileUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=2000)
    skills: Optional[list[str]] = Field(None, max_length=50)
    experience_years: Optional[int] = Field(None, ge=0, le=60)
    education: Optional[list[dict[str, Any]]] = None
    work_experience: Optional[list[dict[str, Any]]] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    resume_url: Optional[str] = Field(None, max_length=500)
    profile_picture_url: Optional[str] = Field(None, max_length=500)


class JobSeekerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[list[str]] = None
    experience_years: Optional[int] = None
    education: Optional[list[dict[str, Any]]] = None
    work_experience: Optional[list[dict[str, Any]]] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    resume_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    profile_completeness: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── Company Profile ─────────────────────────────────────────────────


class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    logo_url: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    profile_picture_url: Optional[str] = Field(None, max_length=500)


class CompanyProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    is_verified: bool
    is_active: bool
    profile_picture_url: Optional[str] = None
    profile_completeness: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── Photo Upload Response ───────────────────────────────────────────


class PhotoUploadResponse(BaseModel):
    url: str
    message: str = "Profile photo uploaded successfully"
