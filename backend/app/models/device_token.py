import enum
import uuid
import hashlib
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DeviceType(str, enum.Enum):
    ios = "ios"
    android = "android"
    web = "web"


def _hash_token(token: str) -> str:
    """SHA-256 hex digest used for unique indexing (avoids btree size limits)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class DeviceToken(Base):
    __tablename__ = "device_tokens"
    __table_args__ = (
        Index("ix_device_tokens_user_id_active", "user_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(Text, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    device_type: Mapped[str] = mapped_column(String(10), nullable=False, default=DeviceType.android)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", viewonly=True)

    def __repr__(self) -> str:
        return f"<DeviceToken {self.id} user={self.user_id} type={self.device_type}>"
