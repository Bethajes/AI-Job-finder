from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BadRequestException, ForbiddenException
from app.models.user import User, UserRole
from app.schemas.profile import (
    CompanyProfileResponse,
    CompanyProfileUpdate,
    JobSeekerProfileResponse,
    JobSeekerProfileUpdate,
    PhotoUploadResponse,
    ProfileCompletenessResponse,
)
from app.services.profile_service import ProfileService
from app.services.upload_service import upload_service
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _get_profile_service(session: AsyncSession) -> ProfileService:
    return ProfileService(session)


# ── Job Seeker Profile ──────────────────────────────────────────────


@router.get("/me/job-seeker", response_model=JobSeekerProfileResponse)
async def get_my_job_seeker_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JobSeekerProfileResponse:
    service = _get_profile_service(session)
    profile = await service.get_job_seeker_profile(current_user.id)
    return profile


@router.put("/me/job-seeker", response_model=JobSeekerProfileResponse)
async def update_my_job_seeker_profile(
    body: JobSeekerProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JobSeekerProfileResponse:
    if current_user.role != UserRole.job_seeker:
        raise ForbiddenException(
            detail="Only job seekers can update a job seeker profile"
        )
    service = _get_profile_service(session)
    data = body.model_dump(exclude_unset=True)
    profile = await service.update_job_seeker_profile(current_user.id, data)
    return profile


@router.post(
    "/me/job-seeker/photo",
    response_model=PhotoUploadResponse,
    status_code=201,
)
async def upload_job_seeker_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PhotoUploadResponse:
    if current_user.role != UserRole.job_seeker:
        raise ForbiddenException(
            detail="Only job seekers can upload a job seeker profile photo"
        )

    url = await upload_service.upload_profile_image(
        file=file,
        folder="profiles/job-seekers",
        user_id=str(current_user.id),
    )

    service = _get_profile_service(session)
    profile = await service.update_job_seeker_profile(
        current_user.id, {"profile_picture_url": url}
    )
    return PhotoUploadResponse(url=url)


@router.get(
    "/me/job-seeker/completeness",
    response_model=ProfileCompletenessResponse,
)
async def get_job_seeker_completeness(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProfileCompletenessResponse:
    service = _get_profile_service(session)
    score, missing = await service.get_job_seeker_completeness(current_user.id)
    return ProfileCompletenessResponse(completeness=score, missing_fields=missing)


# ── Company Profile ─────────────────────────────────────────────────


@router.get("/me/companies", response_model=list[CompanyProfileResponse])
async def list_my_companies(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[CompanyProfileResponse]:
    service = _get_profile_service(session)
    companies = await service.list_company_profiles(current_user.id)
    return companies


@router.get(
    "/me/companies/{company_id}",
    response_model=CompanyProfileResponse,
)
async def get_my_company(
    company_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CompanyProfileResponse:
    import uuid as _uuid

    service = _get_profile_service(session)
    company = await service.get_company_profile(
        current_user.id, _uuid.UUID(company_id)
    )
    return company


@router.put(
    "/me/companies/{company_id}",
    response_model=CompanyProfileResponse,
)
async def update_my_company(
    company_id: str,
    body: CompanyProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CompanyProfileResponse:
    import uuid as _uuid

    if current_user.role != UserRole.employer:
        raise ForbiddenException(
            detail="Only employers can update a company profile"
        )
    service = _get_profile_service(session)
    data = body.model_dump(exclude_unset=True)
    company = await service.update_company_profile(
        current_user.id, _uuid.UUID(company_id), data
    )
    return company


@router.post(
    "/me/companies/{company_id}/photo",
    response_model=PhotoUploadResponse,
    status_code=201,
)
async def upload_company_photo(
    company_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PhotoUploadResponse:
    import uuid as _uuid

    if current_user.role != UserRole.employer:
        raise ForbiddenException(
            detail="Only employers can upload a company profile photo"
        )

    url = await upload_service.upload_profile_image(
        file=file,
        folder="profiles/companies",
        user_id=company_id,
    )

    service = _get_profile_service(session)
    company = await service.update_company_profile(
        current_user.id,
        _uuid.UUID(company_id),
        {"profile_picture_url": url},
    )
    return PhotoUploadResponse(url=url)


@router.get(
    "/me/companies/{company_id}/completeness",
    response_model=ProfileCompletenessResponse,
)
async def get_company_completeness(
    company_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ProfileCompletenessResponse:
    import uuid as _uuid

    service = _get_profile_service(session)
    score, missing = await service.get_company_completeness(
        current_user.id, _uuid.UUID(company_id)
    )
    return ProfileCompletenessResponse(completeness=score, missing_fields=missing)
