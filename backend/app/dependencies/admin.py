"""Admin role-gating dependencies (Week 8).

`require_admin` guards every /admin endpoint. `require_super_admin` is the
stronger gate for destructive/privileged operations, restricted to admins
whose email is listed in settings.SUPER_ADMIN_EMAILS.
"""

from fastapi import Depends

from app.api.v1.dependencies import get_current_user
from app.core.config import settings
from app.core.exceptions import ForbiddenException
from app.models.user import User, UserRole


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the authenticated user has the admin role."""
    if current_user.role != UserRole.admin:
        raise ForbiddenException(detail="Admin access required")
    return current_user


async def require_super_admin(
    current_user: User = Depends(require_admin),
) -> User:
    """Admin whose email is explicitly allow-listed as a super admin."""
    if current_user.email.lower() not in {
        email.lower() for email in settings.SUPER_ADMIN_EMAILS
    }:
        raise ForbiddenException(detail="Super admin access required")
    return current_user
