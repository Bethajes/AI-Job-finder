"""Admin audit log model (Week 8).

One immutable row per privileged action, written in the same transaction
as the change it describes so the trail can never diverge from reality.
"""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AdminLog(Base):
    __tablename__ = "admin_logs"
    __table_args__ = (
        Index("ix_admin_logs_admin_id_created_at", "admin_id", "created_at"),
        Index("ix_admin_logs_action_type", "action_type"),
        Index("ix_admin_logs_resource", "resource_type", "resource_id"),
        Index("ix_admin_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The acting admin. SET NULL keeps history even if the account is later
    # hard-deleted.
    admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # What happened and to what (e.g. user_update / user).
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Structured before/after diff, e.g. {"role": ["job_seeker", "admin"]}.
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Request context for forensics.
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    admin: Mapped[Optional["User"]] = relationship("User", viewonly=True)

    def __repr__(self) -> str:
        return (
            f"<AdminLog {self.action_type} {self.resource_type}"
            f":{self.resource_id} by={self.admin_id}>"
        )
