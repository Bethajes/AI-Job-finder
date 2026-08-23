import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

API = settings.API_V1_PREFIX

REGISTER_PAYLOAD = {
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "securepassword123",
    "role": "job_seeker",
}

REGISTER_PAYLOAD_2 = {
    "email": "employer@example.com",
    "first_name": "Employer",
    "last_name": "Corp",
    "password": "securepassword123",
    "role": "employer",
}


async def _cleanup(session_factory, email: str | None = None) -> None:
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        if email:
            await db.execute(
                text("DELETE FROM users WHERE email = :email"), {"email": email}
            )
        else:
            await db.execute(text("DELETE FROM companies"))
            await db.execute(text("DELETE FROM job_seeker_profiles"))
            await db.execute(text("DELETE FROM users"))
        await db.commit()


@pytest.fixture(autouse=True)
async def cleanup_users():
    await _cleanup(None)
    yield
    await _cleanup(None)


# ── Registration ──────────────────────────────────────────────────────


async def test_register_returns_tokens(client: AsyncClient) -> None:
    resp = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    payload = {**REGISTER_PAYLOAD, "password": "short"}
    resp = await client.post(f"{API}/auth/register", json=payload)
    assert resp.status_code == 422


async def test_register_rejects_invalid_email(client: AsyncClient) -> None:
    payload = {**REGISTER_PAYLOAD, "email": "not-an-email"}
    resp = await client.post(f"{API}/auth/register", json=payload)
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────


async def test_login_returns_tokens(client: AsyncClient) -> None:
    await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient) -> None:
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": "nobody@example.com", "password": "anypassword"},
    )
    assert resp.status_code == 401


# ── Token refresh ─────────────────────────────────────────────────────


async def test_refresh_returns_new_access_token(client: AsyncClient) -> None:
    reg = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body


async def test_refresh_rejects_invalid_token(client: AsyncClient) -> None:
    resp = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": "garbage-token"}
    )
    assert resp.status_code == 401


async def test_refresh_rejects_access_token(client: AsyncClient) -> None:
    reg = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    access_token = reg.json()["access_token"]
    resp = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": access_token}
    )
    assert resp.status_code == 401


# ── Protected /me route ───────────────────────────────────────────────


async def test_me_returns_current_user(client: AsyncClient) -> None:
    reg = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    token = reg.json()["access_token"]
    resp = await client.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["first_name"] == REGISTER_PAYLOAD["first_name"]
    assert body["role"] == "job_seeker"
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body


async def test_me_rejects_no_token(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/auth/me")
    assert resp.status_code in (401, 403)


async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    resp = await client.get(
        f"{API}/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────


async def test_logout_returns_204(client: AsyncClient) -> None:
    reg = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    token = reg.json()["access_token"]
    resp = await client.post(
        f"{API}/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


# ── Relationships ─────────────────────────────────────────────────────


async def test_job_seeker_can_create_profile(client: AsyncClient) -> None:
    reg = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    token = reg.json()["access_token"]
    me_resp = await client.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = me_resp.json()["id"]

    from app.core.database import AsyncSessionLocal
    from app.models.job_seeker import JobSeekerProfile

    async with AsyncSessionLocal() as db:
        profile = JobSeekerProfile(
            user_id=uuid.UUID(user_id),
            title="Software Engineer",
            skills=["Python", "FastAPI", "PostgreSQL"],
            experience_years=5,
            education=[{"degree": "BSc Computer Science", "institution": "AAU"}],
            work_experience=[
                {"company": "TechCorp", "role": "Backend Engineer", "years": 3}
            ],
            city="Addis Ababa",
            country="Ethiopia",
        )
        db.add(profile)
        await db.commit()

    from app.models.user import User

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one()
        await db.refresh(user, ["job_seeker_profile"])
        assert user.job_seeker_profile is not None
        assert user.job_seeker_profile.title == "Software Engineer"
        assert user.job_seeker_profile.skills == ["Python", "FastAPI", "PostgreSQL"]
        assert user.job_seeker_profile.city == "Addis Ababa"


async def test_user_can_own_companies(client: AsyncClient) -> None:
    reg = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD_2)
    token = reg.json()["access_token"]
    me_resp = await client.get(
        f"{API}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = me_resp.json()["id"]

    from app.core.database import AsyncSessionLocal
    from app.models.company import Company

    async with AsyncSessionLocal() as db:
        company = Company(
            owner_id=uuid.UUID(user_id),
            name="Ethiopian Tech",
            slug="ethiopian-tech",
            description="A leading tech company",
            industry="Technology",
            city="Addis Ababa",
            country="Ethiopia",
        )
        db.add(company)
        await db.commit()

    from app.models.user import User

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one()
        await db.refresh(user, ["companies"])
        assert len(user.companies) == 1
        assert user.companies[0].name == "Ethiopian Tech"
        assert user.companies[0].slug == "ethiopian-tech"
