import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.config import settings

API = settings.API_V1_PREFIX

JOB_SEEKER_PAYLOAD = {
    "email": "jobs-seeker@example.com",
    "first_name": "Seeker",
    "last_name": "Tester",
    "password": "securepassword123",
    "role": "job_seeker",
}

EMPLOYER_A_PAYLOAD = {
    "email": "jobs-employer-a@example.com",
    "first_name": "Alpha",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}

EMPLOYER_B_PAYLOAD = {
    "email": "jobs-employer-b@example.com",
    "first_name": "Beta",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}


def _future_deadline(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _job_payload(company_id: str, **overrides) -> dict:
    payload = {
        "title": "Senior Backend Developer",
        "description": "We are looking for an experienced backend developer to join our team.",
        "requirements": ["3+ years with Python", "Experience with FastAPI"],
        "responsibilities": ["Design APIs", "Mentor junior developers"],
        "company_id": company_id,
        "employment_type": "full-time",
        "experience_level": "senior",
        "salary_min": 15000,
        "salary_max": 30000,
        "currency": "ETB",
        "location": "Addis Ababa",
        "is_remote": False,
        "application_deadline": _future_deadline(),
        "category": "Engineering",
        "tags": ["python", "fastapi", "postgresql"],
    }
    payload.update(overrides)
    return payload


async def _cleanup():
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
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


async def _create_company(owner_email: str, name: str, slug: str, **fields) -> str:
    from app.core.database import AsyncSessionLocal
    from app.models.company import Company
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == owner_email))
        user = result.scalar_one()
        company = Company(
            owner_id=user.id,
            name=name,
            slug=slug,
            city="Addis Ababa",
            country="Ethiopia",
            **fields,
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return str(company.id)


async def _create_job(client: AsyncClient, token: str, company_id: str, **overrides) -> dict:
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id, **overrides),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture(autouse=True)
async def cleanup():
    await _cleanup()
    yield
    await _cleanup()


# ── Create ───────────────────────────────────────────────────────────


async def test_create_job_with_valid_data_returns_201(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-jobs"
    )

    job = await _create_job(client, token, company_id)

    assert uuid.UUID(job["id"])
    assert job["title"] == "Senior Backend Developer"
    assert job["status"] == "draft"
    assert job["employment_type"] == "full-time"
    assert job["experience_level"] == "senior"
    assert job["currency"] == "ETB"
    assert job["salary_min"] == 15000.0
    assert job["salary_max"] == 30000.0
    assert job["requirements"] == ["3+ years with Python", "Experience with FastAPI"]
    assert job["company"]["id"] == company_id
    assert job["views_count"] == 0
    assert job["applications_count"] == 0


async def test_create_job_without_auth_returns_401(client: AsyncClient) -> None:
    resp = await client.post(f"{API}/jobs", json=_job_payload(str(uuid.uuid4())))
    assert resp.status_code == 401


async def test_create_job_as_job_seeker_returns_403(client: AsyncClient) -> None:
    await _register(client, EMPLOYER_A_PAYLOAD)
    token = await _register(client, JOB_SEEKER_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Other Corp", "other-corp-jobs"
    )
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id),
    )
    assert resp.status_code == 403


async def test_create_job_for_company_not_owned_returns_403(
    client: AsyncClient,
) -> None:
    await _register(client, EMPLOYER_A_PAYLOAD)
    intruder_token = await _register(client, EMPLOYER_B_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-owned"
    )

    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(intruder_token),
        json=_job_payload(company_id),
    )
    assert resp.status_code == 403


async def test_create_job_for_unknown_company_returns_404(
    client: AsyncClient,
) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(str(uuid.uuid4())),
    )
    assert resp.status_code == 404


# ── Validation ───────────────────────────────────────────────────────


async def test_create_job_rejects_past_deadline(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-validation"
    )

    past = (
        (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    )
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id, application_deadline=past),
    )
    assert resp.status_code == 422


async def test_create_job_rejects_invalid_salary_range(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-salary"
    )

    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id, salary_min=50000, salary_max=10000),
    )
    assert resp.status_code == 422


async def test_create_job_rejects_invalid_employment_type(
    client: AsyncClient,
) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-emptype"
    )

    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id, employment_type="volunteering"),
    )
    assert resp.status_code == 422


# ── Retrieve ─────────────────────────────────────────────────────────


async def test_get_job_details_is_public(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-public"
    )
    job = await _create_job(client, token, company_id)

    # publish so it is publicly visible
    resp = await client.patch(
        f"{API}/jobs/{job['id']}/publish", headers=await _auth_headers(token)
    )
    assert resp.status_code == 200

    anon_resp = await client.get(f"{API}/jobs/{job['id']}")
    assert anon_resp.status_code == 200
    body = anon_resp.json()
    assert body["id"] == job["id"]
    assert body["company"]["name"] == "Alpha Corp"


async def test_draft_job_hidden_from_public_but_visible_to_owner(
    client: AsyncClient,
) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-draft"
    )
    job = await _create_job(client, token, company_id)

    anon_resp = await client.get(f"{API}/jobs/{job['id']}")
    assert anon_resp.status_code == 404

    owner_resp = await client.get(
        f"{API}/jobs/{job['id']}", headers=await _auth_headers(token)
    )
    assert owner_resp.status_code == 200


async def test_get_missing_job_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/jobs/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_view_count_increments_on_public_views(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-views"
    )
    job = await _create_job(client, token, company_id)
    await client.patch(
        f"{API}/jobs/{job['id']}/publish", headers=await _auth_headers(token)
    )

    await client.get(f"{API}/jobs/{job['id']}")
    await client.get(f"{API}/jobs/{job['id']}")

    resp = await client.get(f"{API}/jobs/{job['id']}")
    assert resp.json()["views_count"] == 3


# ── Update ───────────────────────────────────────────────────────────


async def test_update_owned_job_works(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-update"
    )
    job = await _create_job(client, token, company_id)

    resp = await client.put(
        f"{API}/jobs/{job['id']}",
        headers=await _auth_headers(token),
        json={"title": "Lead Backend Engineer", "salary_max": 45000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Lead Backend Engineer"
    assert body["salary_max"] == 45000.0
    assert body["salary_min"] == 15000.0
    assert body["description"] == job["description"]


async def test_update_other_users_job_returns_403(client: AsyncClient) -> None:
    owner_token = await _register(client, EMPLOYER_A_PAYLOAD)
    other_token = await _register(client, EMPLOYER_B_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-update-403"
    )
    job = await _create_job(client, owner_token, company_id)

    resp = await client.put(
        f"{API}/jobs/{job['id']}",
        headers=await _auth_headers(other_token),
        json={"title": "Hijacked Title"},
    )
    assert resp.status_code == 403


async def test_update_job_requires_auth(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-update-auth"
    )
    job = await _create_job(client, token, company_id)

    resp = await client.put(f"{API}/jobs/{job['id']}", json={"title": "Nope"})
    assert resp.status_code == 401


# ── Close / Publish / Delete ────────────────────────────────────────


async def test_close_job_sets_closed_status(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-close"
    )
    job = await _create_job(client, token, company_id)

    resp = await client.patch(
        f"{API}/jobs/{job['id']}/close", headers=await _auth_headers(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "closed"
    assert body["closing_date"] is not None


async def test_close_job_requires_ownership(client: AsyncClient) -> None:
    owner_token = await _register(client, EMPLOYER_A_PAYLOAD)
    other_token = await _register(client, EMPLOYER_B_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-close-403"
    )
    job = await _create_job(client, owner_token, company_id)

    resp = await client.patch(
        f"{API}/jobs/{job['id']}/close", headers=await _auth_headers(other_token)
    )
    assert resp.status_code == 403


async def test_publish_job_makes_it_publicly_listed(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-publish"
    )
    job = await _create_job(client, token, company_id)

    resp = await client.patch(
        f"{API}/jobs/{job['id']}/publish", headers=await _auth_headers(token)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
    assert resp.json()["posted_date"] is not None


async def test_delete_job_soft_deletes_by_closing(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-delete"
    )
    job = await _create_job(client, token, company_id)

    resp = await client.delete(
        f"{API}/jobs/{job['id']}", headers=await _auth_headers(token)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"

    from app.core.database import AsyncSessionLocal
    from app.models.job import Job

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == uuid.UUID(job["id"])))
        stored = result.scalar_one_or_none()
        assert stored is not None, "soft delete must keep the row"
        assert stored.status == "closed"

    owner_resp = await client.get(
        f"{API}/jobs/{job['id']}", headers=await _auth_headers(token)
    )
    assert owner_resp.status_code == 200
    assert owner_resp.json()["status"] == "closed"


async def test_delete_job_requires_ownership(client: AsyncClient) -> None:
    owner_token = await _register(client, EMPLOYER_A_PAYLOAD)
    other_token = await _register(client, EMPLOYER_B_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-corp-delete-403"
    )
    job = await _create_job(client, owner_token, company_id)

    resp = await client.delete(
        f"{API}/jobs/{job['id']}", headers=await _auth_headers(other_token)
    )
    assert resp.status_code == 403


# ── Listing ──────────────────────────────────────────────────────────


async def test_list_jobs_hides_drafts_by_default_and_owner_sees_them(
    client: AsyncClient,
) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    token_b = await _register(client, EMPLOYER_B_PAYLOAD)
    company_a = await _create_company(EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-list")
    company_b_id = await _create_company(EMPLOYER_B_PAYLOAD["email"], "Beta Corp", "beta-list")

    await _create_job(client, token, company_a, title="Alpha Job One")
    await _create_job(client, token, company_a, title="Alpha Job Two")
    await _create_job(client, token_b, company_b_id, title="Beta Job One")

    # Default public listing shows only published jobs; all are drafts here.
    resp = await client.get(f"{API}/jobs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # Owner can list their drafts (including other statuses) for their company.
    owner_resp = await client.get(
        f"{API}/jobs",
        params={"company_id": company_a, "status": "draft"},
        headers=await _auth_headers(token),
    )
    assert owner_resp.status_code == 200
    body = owner_resp.json()
    assert body["total"] == 2
    titles = {item["title"] for item in body["items"]}
    assert titles == {"Alpha Job One", "Alpha Job Two"}

    # The other employer must not see Alpha's drafts.
    intruder_resp = await client.get(
        f"{API}/jobs",
        params={"company_id": company_a, "status": "draft"},
        headers=await _auth_headers(token_b),
    )
    assert intruder_resp.status_code == 403


async def test_list_jobs_by_company_returns_only_that_companys_jobs(
    client: AsyncClient,
) -> None:
    token_a = await _register(client, EMPLOYER_A_PAYLOAD)
    token_b = await _register(client, EMPLOYER_B_PAYLOAD)
    company_a = await _create_company(EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-pub")
    company_b = await _create_company(EMPLOYER_B_PAYLOAD["email"], "Beta Corp", "beta-pub")

    for title in ("Alpha Job One", "Alpha Job Two"):
        job = await _create_job(client, token_a, company_a, title=title)
        pub = await client.patch(
            f"{API}/jobs/{job['id']}/publish", headers=await _auth_headers(token_a)
        )
        assert pub.status_code == 200

    beta_job = await _create_job(client, token_b, company_b, title="Beta Job One")
    await client.patch(
        f"{API}/jobs/{beta_job['id']}/publish", headers=await _auth_headers(token_b)
    )

    resp = await client.get(f"{API}/jobs", params={"company_id": company_a})
    body = resp.json()
    assert body["total"] == 2
    titles = {item["title"] for item in body["items"]}
    assert titles == {"Alpha Job One", "Alpha Job Two"}
    assert all(item["company"]["id"] == company_a for item in body["items"])


async def test_list_jobs_pagination_metadata(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-pagination"
    )
    ids = []
    for i in range(5):
        job = await _create_job(client, token, company_id, title=f"Job Number {i}")
        pub = await client.patch(
            f"{API}/jobs/{job['id']}/publish", headers=await _auth_headers(token)
        )
        assert pub.status_code == 200
        ids.append(job["id"])

    resp = await client.get(
        f"{API}/jobs", params={"page": 2, "page_size": 2, "company_id": company_id}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["page"] == 2
    assert body["page_size"] == 2
    assert body["total_pages"] == 3
    assert len(body["items"]) == 2


async def test_anonymous_cannot_filter_private_statuses(client: AsyncClient) -> None:
    resp = await client.get(
        f"{API}/jobs", params={"status": "draft", "company_id": str(uuid.uuid4())}
    )
    assert resp.status_code == 403


async def test_owner_cannot_filter_private_statuses_of_other_company(
    client: AsyncClient,
) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    await _register(client, EMPLOYER_B_PAYLOAD)
    foreign_company = await _create_company(
        EMPLOYER_B_PAYLOAD["email"], "Beta Corp", "beta-private"
    )
    resp = await client.get(
        f"{API}/jobs",
        params={"company_id": foreign_company, "status": "draft"},
        headers=await _auth_headers(token),
    )
    assert resp.status_code == 403


async def test_list_jobs_search_and_type_filters(client: AsyncClient) -> None:
    token = await _register(client, EMPLOYER_A_PAYLOAD)
    company_id = await _create_company(
        EMPLOYER_A_PAYLOAD["email"], "Alpha Corp", "alpha-search"
    )

    dev = await _create_job(client, token, company_id, title="Python Developer")
    await _create_job(
        client, token, company_id, title="Designer", employment_type="part-time"
    )
    await client.patch(
        f"{API}/jobs/{dev['id']}/publish", headers=await _auth_headers(token)
    )

    resp = await client.get(
        f"{API}/jobs", params={"search": "python", "employment_type": "full-time"}
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Python Developer"
