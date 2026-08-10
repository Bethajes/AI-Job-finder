from typing import Literal

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, Literal["ok"]]:
    """Basic liveness check."""
    return {"status": "ok"}