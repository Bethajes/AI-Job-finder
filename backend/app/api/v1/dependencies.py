import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import verify_token, ACCESS_TOKEN_TYPE
from app.models.user import User
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    token_payload: Optional[dict] = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = UnauthorizedException(
        detail="Not authenticated"
    )

    if token_payload is None:
        raise credentials_exception

    token = token_payload.credentials
    try:
        payload = verify_token(token, expected_type=ACCESS_TOKEN_TYPE)
    except Exception:
        raise UnauthorizedException(detail="Invalid or expired token")

    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    auth_service = AuthService(session)
    try:
        user = await auth_service.get_current_user(uuid.UUID(sub))
    except UnauthorizedException:
        raise
    except Exception:
        raise credentials_exception

    return user
