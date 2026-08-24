"""Reusable pagination primitives for list/search endpoints.

Offset/limit pagination is appropriate for the MVP dataset size
(job postings). If datasets grow large, swap in cursor-based
pagination behind the same response contract.
"""

import math
from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel, ConfigDict

ItemT = TypeVar("ItemT")

DEFAULT_PAGE = 1
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class PaginationParams(BaseModel):
    """Validated page/limit pair shared by paginated endpoints."""

    model_config = ConfigDict(frozen=True)

    page: int = DEFAULT_PAGE
    limit: int = DEFAULT_LIMIT

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit

    @classmethod
    def validate_bounds(cls, page: int = DEFAULT_PAGE, limit: int = DEFAULT_LIMIT) -> "PaginationParams":
        if page < 1:
            raise ValueError("page must be >= 1")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if limit > MAX_LIMIT:
            raise ValueError(f"limit must be <= {MAX_LIMIT}")
        return cls(page=page, limit=limit)


class PageMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[ItemT]):
    """Standard envelope for paginated results."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ItemT]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def build(
        cls,
        items: Sequence[ItemT],
        *,
        total: int,
        page: int,
        limit: int,
    ) -> "PaginatedResponse[ItemT]":
        return cls(items=list(items), **compute_pagination(total=total, page=page, limit=limit))


def compute_pagination(*, total: int, page: int, limit: int) -> dict[str, Any]:
    """Compute pagination metadata shared by paginated response models."""
    pages = max(1, math.ceil(total / limit)) if limit > 0 else 1
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "has_next": page < pages,
        "has_previous": page > 1,
    }
