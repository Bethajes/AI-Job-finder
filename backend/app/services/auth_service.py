import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
    REFRESH_TOKEN_TYPE,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(
        self,
        *,
        email: str,
        phone: Optional[str],
        first_name: str,
        last_name: str,
        password: str,
        role: UserRole = UserRole.job_seeker,
    ) -> tuple[User, TokenResponse]:
        existing = await self.user_repo.get_by_email(email)
        if existing is not None:
            raise ConflictException(detail="An account with this email already exists")

        hashed = get_password_hash(password)
        user = await self.user_repo.create(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed,
            role=role.value,
        )
        await self.session.commit()

        tokens = self._create_tokens(user)
        return user, tokens

    async def login(
        self,
        *,
        email: str,
        password: str,
    ) -> tuple[User, TokenResponse]:
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise UnauthorizedException(detail="Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException(detail="Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException(detail="This account has been deactivated")

        await self.user_repo.update_last_login(user)
        await self.session.commit()

        tokens = self._create_tokens(user)
        return user, tokens

    async def refresh(self, *, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
        sub = payload.get("sub")
        if sub is None:
            raise UnauthorizedException(detail="Invalid refresh token")

        user = await self.user_repo.get_by_id(uuid.UUID(sub))
        if user is None:
            raise UnauthorizedException(detail="User not found")

        if not user.is_active:
            raise UnauthorizedException(detail="This account has been deactivated")

        tokens = self._create_tokens(user)
        return tokens

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedException(detail="User not found")
        if not user.is_active:
            raise UnauthorizedException(detail="This account has been deactivated")
        return user

    @staticmethod
    def _create_tokens(user: User) -> TokenResponse:
        subject = str(user.id)
        return TokenResponse(
            access_token=create_access_token(subject),
            refresh_token=create_refresh_token(subject),
        )
