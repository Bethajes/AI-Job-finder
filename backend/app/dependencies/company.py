"""Company ownership and verification dependencies for employer actions."""
import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.company import Company
from app.models.job import Job
from app.models.user import User, UserRole


async def require_employer(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user has the employer role."""
    if current_user.role != UserRole.employer:
        raise ForbiddenException(
            detail="Only employers can perform this action"
        )
    return current_user


async def verify_company_ownership(
    session: AsyncSession,
    *,
    user: User,
    company_id: uuid.UUID,
    require_verified: bool = False,
) -> Company:
    """
    Verify that `user` is an active employer who owns an active company.

    Raises 404 if the company does not exist and 403 when the company is not
    owned by the user or fails activation/verification checks.
    """
    if user.role != UserRole.employer:
        raise ForbiddenException(detail="Only employers can manage job postings")

    result = await session.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if company is None:
        raise NotFoundException(detail="Company not found")

    if company.owner_id != user.id:
        raise ForbiddenException(
            detail="You do not have permission to manage jobs for this company"
        )
    if not company.is_active:
        raise ForbiddenException(detail="Company account is inactive")
    if require_verified and not company.is_verified:
        raise ForbiddenException(
            detail="Company must be verified to perform this action"
        )
    return company


async def get_verified_company(
    company_id: uuid.UUID,
    current_user: User = Depends(require_employer),
    session: AsyncSession = Depends(get_db),
) -> Company:
    """
    Dependency form of `verify_company_ownership` for routes that receive a
    `company_id` path/query parameter. Returns the owned company or raises.
    """
    return await verify_company_ownership(session, user=current_user, company_id=company_id)


async def ensure_can_manage_job(
    session: AsyncSession,
    *,
    user: User,
    job: Job,
) -> Company:
    """Verify the user owns the company the given job belongs to."""
    if user.role != UserRole.employer:
        raise ForbiddenException(detail="Only employers can manage job postings")
    if job.posted_by_id != user.id:
        raise ForbiddenException(
            detail="You can only manage jobs posted by your own account"
        )
    return await verify_company_ownership(session, user=user, company_id=job.company_id)
