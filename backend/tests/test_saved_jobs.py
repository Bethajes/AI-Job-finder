"""Week 7: saved-jobs endpoints tests."""

import logging

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.config import settings

API = settings.API_V1_PREFIX

SEEKER = {
    "email": "saved-seeker@example.com",
    "first_name": "Alice",
    "last_name": "Saved",
    "password": "securepassword123",
    "role": "job_seeker",
}

EMPLOYER = {
    "email": "saved-employer@example.com",
    "first_name": "Bob",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}


def _future_deadline(days: int = 30) -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _job_payload(company_id: str) -> dict:
    return {
        "title": "Software Engineer",
        "description": "An exciting software engineering role.",
        "company_id": company_id,
        "employment_type": "full-time",
        "experience_level": "mid",
        "location": "Addis Ababa",
        "application_deadline": _future_deadline(),
    }


async def _cleanup() -> None:
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM saved_jobs"))
        await db.execute(text("DELETE FROM device_tokens"))
        await db.execute(text("DELETE FROM applications"))
        await db.execute(text("DELETE FROM jobs"))
        await db.execute(text("DELETE FROM companies"))
        await db.execute(text("DELETE FROM job_seeker_profiles"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()


async def _register(client: AsyncClient, payload: dict) -> str:
    resp = await client.post(f"{API}/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


async def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_company(owner_email: str, name: str, slug: str) -> str:
    from app.core.database import AsyncSessionLocal
    from app.models.company import Company
    from app.models.user import User
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == owner_email))
        user = result.scalar_one()
        company = Company(owner_id=user.id, name=name, slug=slug)
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return str(company.id)


async def _create_published_job(client: AsyncClient, token: str, company_id: str) -> dict:
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id),
    )
    assert resp.status_code == 201, resp.text
    job = resp.json()
    resp = await client.patch(
        f"{API}/jobs/{job['id']}/publish",
        headers=await _auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(autouse=True)
async def cleanup():
    await _cleanup()
    yield
    await _cleanup()


# ── Save job ────────────────────────────────────────────────────────────


async def test_save_job_returns_201(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")
    job = await _create_published_job(client, employer_token, company_id)

    resp = await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["job_id"] == job["id"]
    assert data["message"] == "Job saved"


async def test_save_job_already_saved_returns_409(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")
    job = await _create_published_job(client, employer_token, company_id)

    resp = await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 201, resp.text

    resp = await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 409, resp.text


async def test_save_nonexistent_job_returns_404(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    import uuid
    fake_id = str(uuid.uuid4())

    resp = await client.post(
        f"{API}/saved-jobs/{fake_id}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 404, resp.text


async def test_save_draft_job_returns_400(client: AsyncClient):
    """Saving a draft (non-published) job should fail."""
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")
    # Create but do NOT publish
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(employer_token),
        json=_job_payload(company_id),
    )
    assert resp.status_code == 201, resp.text
    job = resp.json()

    resp = await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 400, resp.text


# ── Unsave job ──────────────────────────────────────────────────────────


async def test_unsave_job_returns_200(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")
    job = await _create_published_job(client, employer_token, company_id)

    # Save first
    await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )

    resp = await client.delete(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 200, resp.text
    assert "removed" in resp.json()["message"].lower()


async def test_unsave_nonexistent_job_returns_200_gracefully(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    import uuid
    fake_id = str(uuid.uuid4())

    resp = await client.delete(
        f"{API}/saved-jobs/{fake_id}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 200, resp.text
    assert "not" in resp.json()["message"].lower()


# ── List saved jobs ─────────────────────────────────────────────────────


async def test_list_saved_jobs_returns_empty_initially(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    resp = await client.get(
        f"{API}/saved-jobs/me",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_saved_jobs_shows_only_own(client: AsyncClient):
    """Users only see their own saved jobs, not those of other users."""
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")
    job = await _create_published_job(client, employer_token, company_id)

    # Employer saves the job
    await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(employer_token),
    )

    # Seeker should see nothing
    resp = await client.get(
        f"{API}/saved-jobs/me",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 0


async def test_list_saved_jobs_returns_job_details(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")
    job = await _create_published_job(client, employer_token, company_id)

    await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )

    resp = await client.get(
        f"{API}/saved-jobs/me",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["job_id"] == job["id"]
    assert item["is_active"] is True
    assert "job" in item
    assert item["job"]["title"] == "Software Engineer"
    assert item["job"]["company_name"] == "Acme"


async def test_list_saved_jobs_sorted_newest_first(client: AsyncClient):
    """Saved jobs should be ordered by created_at descending."""
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")

    job1_resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(employer_token),
        json=_job_payload(company_id),
    )
    await client.patch(
        f"{API}/jobs/{job1_resp.json()['id']}/publish",
        headers=await _auth_headers(employer_token),
    )
    job1 = job1_resp.json()

    job2_resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(employer_token),
        json={**_job_payload(company_id), "title": "Backend Dev"},
    )
    await client.patch(
        f"{API}/jobs/{job2_resp.json()['id']}/publish",
        headers=await _auth_headers(employer_token),
    )
    job2 = job2_resp.json()

    # Save in order: job1 first, job2 second
    await client.post(
        f"{API}/saved-jobs/{job1['id']}",
        headers=await _auth_headers(seeker_token),
    )
    await client.post(
        f"{API}/saved-jobs/{job2['id']}",
        headers=await _auth_headers(seeker_token),
    )

    resp = await client.get(
        f"{API}/saved-jobs/me",
        headers=await _auth_headers(seeker_token),
    )
    items = resp.json()["items"]
    assert len(items) == 2
    # Newest first: job2 (second saved) should come first
    assert items[0]["job_id"] == job2["id"]
    assert items[1]["job_id"] == job1["id"]


async def test_list_saved_jobs_pagination(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")

    job_ids = []
    for i in range(5):
        resp = await client.post(
            f"{API}/jobs",
            headers=await _auth_headers(employer_token),
            json={**_job_payload(company_id), "title": f"Job {i}"},
        )
        jid = resp.json()["id"]
        await client.patch(
            f"{API}/jobs/{jid}/publish",
            headers=await _auth_headers(employer_token),
        )
        await client.post(
            f"{API}/saved-jobs/{jid}",
            headers=await _auth_headers(seeker_token),
        )
        job_ids.append(jid)

    resp = await client.get(
        f"{API}/saved-jobs/me?page=1&limit=2",
        headers=await _auth_headers(seeker_token),
    )
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["pages"] == 3
    assert data["has_next"] is True
    assert data["has_previous"] is False


# ── Unauthenticated ─────────────────────────────────────────────────────


async def test_save_job_unauthenticated_returns_401(client: AsyncClient):
    import uuid
    resp = await client.post(f"{API}/saved-jobs/{uuid.uuid4()}")
    assert resp.status_code == 401


async def test_list_saved_jobs_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get(f"{API}/saved-jobs/me")
    assert resp.status_code == 401


# ── Unsave and re-save (reactivate) ─────────────────────────────────────


async def test_unsave_and_resave_reactivates(client: AsyncClient):
    seeker_token = await _register(client, SEEKER)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme", "acme")
    job = await _create_published_job(client, employer_token, company_id)

    resp = await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 201

    await client.delete(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )

    # Re-save: should be 201 (newly reactivated)
    resp = await client.post(
        f"{API}/saved-jobs/{job['id']}",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.status_code == 201, resp.text
    assert "saved" in resp.json()["message"].lower()

    # List should show it again
    resp = await client.get(
        f"{API}/saved-jobs/me",
        headers=await _auth_headers(seeker_token),
    )
    assert resp.json()["total"] == 1
