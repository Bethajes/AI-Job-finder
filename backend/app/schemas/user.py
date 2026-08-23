import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class JobSeekerProfileCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = None
    skills: Optional[list[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=60)
    education: Optional[list[dict[str, Any]]] = None
    work_experience: Optional[list[dict[str, Any]]] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    resume_url: Optional[str] = Field(None, max_length=500)


class JobSeekerProfileUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = None
    skills: Optional[list[str]] = None
    experience_years: Optional[int] = Field(None, ge=0, le=60)
    education: Optional[list[dict[str, Any]]] = None
    work_experience: Optional[list[dict[str, Any]]] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    resume_url: Optional[str] = Field(None, max_length=500)


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
    created_at: datetime
    updated_at: datetime


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)


class CompanyResponse(BaseModel):
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
    created_at: datetime
    updated_at: datetime
