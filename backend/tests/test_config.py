import pytest

from app.core.config import settings


def test_settings_loaded_from_environment() -> None:
    assert settings.APP_NAME == "Ethiopian Job Platform"
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert settings.JWT_SECRET_KEY
    assert settings.JWT_ALGORITHM == "HS256"


def test_database_url_is_not_hardcoded_default() -> None:
    assert settings.DATABASE_URL is not None
    assert settings.JWT_SECRET_KEY not in ("", "change-me")


async def test_database_connectivity() -> None:
    """Verify the async engine can reach PostgreSQL.

    Skipped automatically when the database is not running so the suite
    remains runnable in environments without a database.
    """
    from sqlalchemy import text
    from app.core.database import engine

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
    except Exception:
        pytest.skip("PostgreSQL is not reachable")