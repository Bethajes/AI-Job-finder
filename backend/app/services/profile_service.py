from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.company import Company
from app.models.job_seeker import JobSeekerProfile
from app.models.user import User


# Weights for job seeker profile completeness
JOB_SEEKER_FIELDS: dict[str, int] = {
    "title": 15,
    "bio": 15,
    "skills": 15,
    "experience_years": 10,
    "education": 10,
    "work_experience": 10,
    "city": 5,
    "country": 5,
    "resume_url": 5,
    "profile_picture_url": 10,
}

# Weights for company profile completeness
COMPANY_FIELDS: dict[str, int] = {
    "description": 25,
    "logo_url": 20,
    "city": 15,
    "country": 15,
    "industry": 15,
    "profile_picture_url": 10,
}


def _field_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    return True


def calculate_completeness(
    profile: JobSeekerProfile | Company,
    field_weights: dict[str, int],
) -> tuple[int, list[str]]:
    total = 0
    missing: list[str] = []
    for field, weight in field_weights.items():
        value = getattr(profile, field, None)
        if _field_present(value):
            total += weight
        else:
            missing.append(field)
    return total, missing


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Job Seeker Profile ─────────────────────────────────────────────

    async def get_job_seeker_profile(self, user_id: UUID) -> JobSeekerProfile:
        result = await self.session.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise NotFoundException(detail="Job seeker profile not found")
        return profile

    async def create_job_seeker_profile(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> JobSeekerProfile:
        result = await self.session.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise BadRequestException(
                detail="Job seeker profile already exists. Use PUT to update."
            )

        profile = JobSeekerProfile(user_id=user_id, **data)
        self.session.add(profile)
        await self.session.flush()
        score, _ = calculate_completeness(profile, JOB_SEEKER_FIELDS)
        profile.profile_completeness = score
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update_job_seeker_profile(
        self,
        user_id: UUID,
        data: dict[str, Any],
    ) -> JobSeekerProfile:
        result = await self.session.execute(
            select(JobSeekerProfile).where(JobSeekerProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if profile is None:
            profile = JobSeekerProfile(user_id=user_id, **data)
            self.session.add(profile)
        else:
            for key, value in data.items():
                if value is not None:
                    setattr(profile, key, value)

        score, _ = calculate_completeness(profile, JOB_SEEKER_FIELDS)
        profile.profile_completeness = score
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_job_seeker_completeness(
        self, user_id: UUID
    ) -> tuple[int, list[str]]:
        profile = await self.get_job_seeker_profile(user_id)
        return calculate_completeness(profile, JOB_SEEKER_FIELDS)

    # ── Company Profile ────────────────────────────────────────────────

    async def get_company_profile(
        self, user_id: UUID, company_id: UUID
    ) -> Company:
        result = await self.session.execute(
            select(Company).where(
                Company.id == company_id,
                Company.owner_id == user_id,
            )
        )
        company = result.scalar_one_or_none()
        if company is None:
            raise NotFoundException(detail="Company not found")
        return company

    async def list_company_profiles(self, user_id: UUID) -> list[Company]:
        result = await self.session.execute(
            select(Company)
            .where(Company.owner_id == user_id)
            .order_by(Company.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_company_profile(
        self,
        user_id: UUID,
        company_id: UUID,
        data: dict[str, Any],
    ) -> Company:
        company = await self.get_company_profile(user_id, company_id)
        for key, value in data.items():
            if value is not None:
                setattr(company, key, value)
        score, _ = calculate_completeness(company, COMPANY_FIELDS)
        company.profile_completeness = score
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def get_company_completeness(
        self, user_id: UUID, company_id: UUID
    ) -> tuple[int, list[str]]:
        company = await self.get_company_profile(user_id, company_id)
        return calculate_completeness(company, COMPANY_FIELDS)
