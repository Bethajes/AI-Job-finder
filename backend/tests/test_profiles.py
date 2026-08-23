import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    EMAIL_VERIFICATION_TOKEN_TYPE,
)

API = settings.API_V1_PREFIX

JOB_SEEKER_PAYLOAD = {
    "email": "profile-tester@example.com",
    "first_name": "Profile",
    "last_name": "Tester",
    "password": "securepassword123",
    "role": "job_seeker",
}

EMPLOYER_PAYLOAD = {
    "email": "employer-profile@example.com",
    "first_name": "Employer",
    "last_name": "Corp",
    "password": "securepassword123",
    "role": "employer",
}


async def _cleanup():
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM companies"))
        await db.execute(text("DELETE FROM job_seeker_profiles"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()


async def _register(client: AsyncClient, payload: dict) -> str:
    resp = await client.post(f"{API}/auth/register", json=payload)
    return resp.json()["access_token"]


async def _get_user_id(client: AsyncClient, token: str) -> str:
    resp = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()["id"]


@pytest.fixture(autouse=True)
async def cleanup():
    await _cleanup()
    yield
    await _cleanup()


# ── Job Seeker Profile CRUD ──────────────────────────────────────────


async def test_get_job_seeker_profile_returns_404_when_not_created(
    client: AsyncClient,
) -> None:
    token = await _register(client, JOB_SEEKER_PAYLOAD)
    resp = await client.get(
        f"{API}/profiles/me/job-seeker",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


async def test_update_job_seeker_profile_creates_and_updates(
    client: AsyncClient,
) -> None:
    token = await _register(client, JOB_SEEKER_PAYLOAD)
    headers = {"Authorization": f"Bearer {token}"}

    update = {
        "title": "Senior Python Developer",
        "bio": "Experienced developer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience_years": 5,
        "city": "Addis Ababa",
        "country": "Ethiopia",
    }
    resp = await client.put(
        f"{API}/profiles/me/job-seeker", headers=headers, json=update
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Senior Python Developer"
    assert body["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert body["city"] == "Addis Ababa"
    assert body["profile_completeness"] is not None
    assert body["profile_completeness"] > 0

    resp2 = await client.get(
        f"{API}/profiles/me/job-seeker", headers=headers
    )
    assert resp2.status_code == 200
    assert resp2.json()["title"] == "Senior Python Developer"


async def test_update_job_seeker_profile_preserves_existing_fields(
    client: AsyncClient,
) -> None:
    token = await _register(client, JOB_SEEKER_PAYLOAD)
    headers = {"Authorization": f"Bearer {token}"}

    await client.put(
        f"{API}/profiles/me/job-seeker",
        headers=headers,
        json={"title": "Dev", "bio": "Bio"},
    )
    resp = await client.put(
        f"{API}/profiles/me/job-seeker",
        headers=headers,
        json={"title": "Senior Dev"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Senior Dev"
    assert body["bio"] == "Bio"


async def test_employer_cannot_update_job_seeker_profile(
    client: AsyncClient,
) -> None:
    token = await _register(client, EMPLOYER_PAYLOAD)
    resp = await client.put(
        f"{API}/profiles/me/job-seeker",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Nope"},
    )
    assert resp.status_code == 403


# ── Company Profile CRUD ─────────────────────────────────────────────


async def test_list_companies_empty(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_PAYLOAD)
    resp = await client.get(
        f"{API}/profiles/me/companies",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_update_company_profile(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_PAYLOAD)
    headers = {"Authorization": f"Bearer {token}"}

    from app.core.database import AsyncSessionLocal
    from app.models.company import Company
    from app.models.user import User

    user_id = await _get_user_id(client, token)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == EMPLOYER_PAYLOAD["email"])
        )
        user = result.scalar_one()
        company = Company(
            owner_id=user.id,
            name="Test Company",
            slug="test-company-week3",
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        company_id = str(company.id)

    resp = await client.put(
        f"{API}/profiles/me/companies/{company_id}",
        headers=headers,
        json={
            "description": "A great company",
            "industry": "Technology",
            "city": "Addis Ababa",
            "country": "Ethiopia",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "A great company"
    assert body["industry"] == "Technology"
    assert body["profile_completeness"] is not None
    assert body["profile_completeness"] > 0


async def test_get_company(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_PAYLOAD)
    headers = {"Authorization": f"Bearer {token}"}

    from app.core.database import AsyncSessionLocal
    from app.models.company import Company
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == EMPLOYER_PAYLOAD["email"])
        )
        user = result.scalar_one()
        company = Company(
            owner_id=user.id,
            name="Get Me Company",
            slug="get-me-company-week3",
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        company_id = str(company.id)

    resp = await client.get(
        f"{API}/profiles/me/companies/{company_id}", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Me Company"


async def test_job_seeker_cannot_update_company(client: AsyncClient) -> None:
    token = await _register(client, JOB_SEEKER_PAYLOAD)
    headers = {"Authorization": f"Bearer {token}"}

    fake_id = str(uuid.uuid4())
    resp = await client.put(
        f"{API}/profiles/me/companies/{fake_id}",
        headers=headers,
        json={"name": "Nope"},
    )
    assert resp.status_code == 403


# ── Profile Completeness ─────────────────────────────────────────────


async def test_job_seeker_completeness_starts_at_zero(client: AsyncClient) -> None:
    token = await _register(client, JOB_SEEKER_PAYLOAD)
    headers = {"Authorization": f"Bearer {token}"}

    await client.put(
        f"{API}/profiles/me/job-seeker",
        headers=headers,
        json={"title": "Dev"},
    )
    resp = await client.get(
        f"{API}/profiles/me/job-seeker/completeness", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["completeness"] <= 100
    assert isinstance(body["missing_fields"], list)
    assert "title" not in body["missing_fields"]


async def test_completeness_updates_after_profile_change(client: AsyncClient) -> None:
    token = await _register(client, JOB_SEEKER_PAYLOAD)
    headers = {"Authorization": f"Bearer {token}"}

    await client.put(
        f"{API}/profiles/me/job-seeker",
        headers=headers,
        json={"title": "Dev"},
    )
    resp1 = await client.get(
        f"{API}/profiles/me/job-seeker/completeness", headers=headers
    )
    score1 = resp1.json()["completeness"]

    await client.put(
        f"{API}/profiles/me/job-seeker",
        headers=headers,
        json={"title": "Senior Dev", "bio": "Long bio", "skills": ["Python"]},
    )
    resp2 = await client.get(
        f"{API}/profiles/me/job-seeker/completeness", headers=headers
    )
    score2 = resp2.json()["completeness"]
    assert score2 > score1
