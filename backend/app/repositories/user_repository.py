import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        email: str,
        phone: Optional[str],
        first_name: str,
        last_name: str,
        hashed_password: str,
        role: str = "job_seeker",
    ) -> User:
        user = User(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed_password,
            role=role,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()

    async def list_users(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[User], int]:
        count_result = await self.session.execute(select(func.count(User.id)))
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        users = result.scalars().all()
        return users, total

    async def update_last_login(self, user: User) -> User:
        user.last_login = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(user)
        return user
