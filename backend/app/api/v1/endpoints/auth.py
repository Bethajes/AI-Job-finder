from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BadRequestException
from app.core.rate_limit import rate_limit
from app.core.security import (
    EMAIL_VERIFICATION_TOKEN_TYPE,
    create_access_token,
    create_email_verification_token,
    verify_token,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.api.v1.dependencies import get_current_user
from app.utils.email_templates import (
    resend_verification_html,
    verification_email_html,
    welcome_email_html,
)

router = APIRouter(prefix="/auth", tags=["auth"])

email_service = EmailService()


def _verification_url(token: str) -> str:
    base = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
    return f"{base}/auth/verify-email?token={token}"


async def _send_verification_email(
    user: User,
    background_tasks: BackgroundTasks,
) -> None:
    token = create_email_verification_token(str(user.id), user.email)
    url = _verification_url(token)
    subject, html = verification_email_html(url, user.first_name)
    background_tasks.add_task(
        email_service.send_email,
        to=user.email,
        subject=subject,
        html=html,
    )


async def _send_welcome_email(
    user: User,
    background_tasks: BackgroundTasks,
) -> None:
    subject, html = welcome_email_html(user.first_name)
    background_tasks.add_task(
        email_service.send_email,
        to=user.email,
        subject=subject,
        html=html,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    _rl=rate_limit("auth"),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(session)
    user, tokens = await auth_service.register(
        email=body.email,
        phone=body.phone,
        first_name=body.first_name,
        last_name=body.last_name,
        password=body.password,
        role=body.role,
    )
    await _send_verification_email(user, background_tasks)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    _rl=rate_limit("auth"),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(session)
    _user, tokens = await auth_service.login(
        email=body.email,
        password=body.password,
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    auth_service = AuthService(session)
    tokens = await auth_service.refresh(refresh_token=body.refresh_token)
    return tokens


@router.post("/logout", status_code=204)
async def logout(
    _current_user: User = Depends(get_current_user),
) -> None:
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


# ── Email Verification ───────────────────────────────────────────────


class VerifyEmailRequest(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    body: VerifyEmailRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:
    try:
        payload = verify_token(body.token, expected_type=EMAIL_VERIFICATION_TOKEN_TYPE)
    except Exception:
        raise BadRequestException(detail="Invalid or expired verification token")

    sub = payload.get("sub")
    if sub is None:
        raise BadRequestException(detail="Invalid verification token")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(sub)
    if user is None:
        raise BadRequestException(detail="User not found")

    if user.is_verified:
        return MessageResponse(message="Email is already verified")

    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    await session.commit()

    await _send_welcome_email(user, background_tasks)
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    if current_user.is_verified:
        return MessageResponse(message="Email is already verified")

    token = create_email_verification_token(str(current_user.id), current_user.email)
    url = _verification_url(token)
    subject, html = resend_verification_html(url, current_user.first_name)
    background_tasks.add_task(
        email_service.send_email,
        to=current_user.email,
        subject=subject,
        html=html,
    )
    return MessageResponse(message="Verification email sent")
