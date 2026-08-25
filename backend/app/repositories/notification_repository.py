"""Device token CRUD operations (Week 7)."""

import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_token import DeviceToken, _hash_token


class DeviceTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_token(
        self,
        user_id: uuid.UUID,
        token: str,
        device_type: str,
    ) -> DeviceToken:
        """Register a device token, re-assigning ownership if the same token
        already belongs to a different user.

        Returns the (possibly updated) ``DeviceToken`` instance.
        """
        token_hash = _hash_token(token)
        result = await self.session.execute(
            select(DeviceToken).where(DeviceToken.token_hash == token_hash)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.user_id = user_id
            existing.device_type = device_type
            existing.is_active = True
            existing.token = token
            await self.session.flush()
            return existing

        device_token = DeviceToken(
            user_id=user_id,
            token=token,
            token_hash=token_hash,
            device_type=device_type,
        )
        self.session.add(device_token)
        await self.session.flush()
        await self.session.refresh(device_token)
        return device_token

    async def get_by_token_hash(self, token_hash: str) -> Optional[DeviceToken]:
        result = await self.session.execute(
            select(DeviceToken).where(DeviceToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_active_tokens_for_user(
        self, user_id: uuid.UUID
    ) -> Sequence[str]:
        """Return the raw token strings for all active devices of a user."""
        result = await self.session.execute(
            select(DeviceToken.token).where(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active.is_(True),
            )
        )
        return result.scalars().all()

    async def deactivate_by_token(self, token: str) -> bool:
        """Deactivate a device token.  Returns True if a row was affected."""
        token_hash = _hash_token(token)
        result = await self.session.execute(
            select(DeviceToken).where(DeviceToken.token_hash == token_hash)
        )
        device_token = result.scalar_one_or_none()
        if device_token is None:
            return False
        await self.session.delete(device_token)
        await self.session.flush()
        return True

    async def deactivate_tokens(self, token_hashes: list[str]) -> None:
        """Deactivate a batch of invalid tokens (called after FCM errors)."""
        if not token_hashes:
            return
        from sqlalchemy import update

        await self.session.execute(
            update(DeviceToken)
            .where(DeviceToken.token_hash.in_(token_hashes))
            .values(is_active=False)
        )
        await self.session.flush()
