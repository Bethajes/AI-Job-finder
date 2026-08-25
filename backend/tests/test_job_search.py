"""Week 5: Job search, filtering, sorting and pagination tests."""

import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.config import settings

API = settings.API_V1_PREFIX

EMPLOYER_PAYLOAD = {
    "email": "search-employer@example.com",
    "first_name": "Search",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}


def _future_deadline(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _job_payload(company_id: str, **overrides) -> dict:
    payload = {
        "title": "Senior Software Engineer",
        "description": (
            "We are looking for a software engineer to build scalable "
            "backend systems with Python and PostgreSQL."
        ),
        "requirements": ["5+ years with Python", "SQL experience"],
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
        "tags": ["python", "backend"],
    }
    payload.update(overrides)
    return payload


async def _cleanup() -> None:
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


async def _create_company(name: str = "Search Corp", slug: str = "search-corp") -> str:
    from app.core.database import AsyncSessionLocal
    from app.models.company import Company
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == EMPLOYER_PAYLOAD["email"])
        )
        user = result.scalar_one()
        company = Company(owner_id=user.id, name=name, slug=slug)
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return str(company.id)


async def _create_published_job(
    client: AsyncClient, token: str, company_id: str, **overrides
) -> dict:
    """Create + publish a job; returns the created job JSON."""
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id, **overrides),
    )
    assert resp.status_code == 201, resp.text
    job = resp.json()
    resp = await client.patch(
        f"{API}/jobs/{job['id']}/publish", headers=await _auth_headers(token)
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _backdate_job(job_id: str, days: int) -> None:
    from app.core.database import AsyncSessionLocal
    from app.models.job import Job

    posted = datetime.now(timezone.utc) - timedelta(days=days)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = result.scalar_one()
        job.posted_date = posted
        await db.commit()


@pytest.fixture(autouse=True)
async def cleanup():
    await _cleanup()
    yield
    await _cleanup()


@pytest.fixture
async def employer_token(client: AsyncClient) -> str:
    return await _register(client, EMPLOYER_PAYLOAD)


# ── Full-text search ─────────────────────────────────────────────────


async def test_search_finds_relevant_jobs(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="search-relevant")
    await _create_published_job(client, employer_token, company_id)

    resp = await client.get(f"{API}/jobs/search", params={"q": "software engineer"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    titles = [item["title"] for item in body["items"]]
    assert "Senior Software Engineer" in titles
    # Relevance score is populated when searching
    assert all(item["relevance_score"] is not None for item in body["items"])


async def test_search_ranks_title_matches_above_description(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="search-ranking")
    title_match = await _create_published_job(
        client,
        employer_token,
        company_id,
        title="Data Engineer",
        description="General engineering role.",
    )
    description_match = await _create_published_job(
        client,
        employer_token,
        company_id,
        title="Office Administrator",
        description="Looking for a data engineer mindset to organize spreadsheets.",
    )

    resp = await client.get(f"{API}/jobs/search", params={"q": "data engineer"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    ids = [item["id"] for item in items]
    assert title_match["id"] in ids
    assert description_match["id"] in ids
    # Title carries weight 'A' so it must outrank a description-only match.
    assert ids.index(title_match["id"]) < ids.index(description_match["id"])
    scores = [item["relevance_score"] for item in items]
    assert scores[ids.index(title_match["id"])] > scores[
        ids.index(description_match["id"])
    ]


async def test_search_no_results_returns_empty_with_total_zero(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="search-empty")
    await _create_published_job(client, employer_token, company_id)

    resp = await client.get(f"{API}/jobs/search", params={"q": "zzznonexistent"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["pages"] == 1


async def test_draft_jobs_are_not_searchable(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="search-drafts")
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(employer_token),
        json=_job_payload(company_id),
    )
    assert resp.status_code == 201  # stays draft (not published)

    resp = await client.get(f"{API}/jobs/search", params={"q": "software"})
    assert resp.json()["total"] == 0


# ── Filters ──────────────────────────────────────────────────────────


async def test_filter_by_employment_type(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="filter-emptype")
    full_time = await _create_published_job(
        client, employer_token, company_id, employment_type="full-time"
    )
    await _create_published_job(
        client, employer_token, company_id, employment_type="part-time", title="Part Timer"
    )

    resp = await client.get(
        f"{API}/jobs/search", params={"employment_type": "full-time"}
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == full_time["id"]
    assert items[0]["employment_type"] == "full-time"


async def test_filter_by_experience_level(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="filter-explevel")
    senior = await _create_published_job(
        client, employer_token, company_id, experience_level="senior"
    )
    await _create_published_job(
        client, employer_token, company_id, experience_level="entry", title="Junior Dev"
    )

    resp = await client.get(f"{API}/jobs/search", params={"experience_level": "senior"})
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [senior["id"]]


async def test_filter_by_salary_min_uses_overlap(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="filter-salary")
    high = await _create_published_job(
        client,
        employer_token,
        company_id,
        salary_min=20000,
        salary_max=40000,
        title="High Payer",
    )
    await _create_published_job(
        client,
        employer_token,
        company_id,
        salary_min=3000,
        salary_max=8000,
        title="Low Payer",
    )

    resp = await client.get(f"{API}/jobs/search", params={"salary_min": 10000})
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [high["id"]]

    resp = await client.get(f"{API}/jobs/search", params={"salary_max": 10000})
    items = resp.json()["items"]
    assert [i["title"] for i in items] == ["Low Payer"]


async def test_filter_by_location_partial_match(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="filter-location")
    addis = await _create_published_job(
        client, employer_token, company_id, location="Addis Ababa"
    )
    await _create_published_job(
        client, employer_token, company_id, location="Hawassa", title="Hawassa Role"
    )

    resp = await client.get(f"{API}/jobs/search", params={"location": "addis"})
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [addis["id"]]


async def test_filter_by_is_remote(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="filter-remote")
    remote_job = await _create_published_job(
        client, employer_token, company_id, is_remote=True, title="Remote Gigger"
    )
    await _create_published_job(
        client, employer_token, company_id, is_remote=False
    )

    resp = await client.get(f"{API}/jobs/search", params={"is_remote": True})
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [remote_job["id"]]
    assert items[0]["is_remote"] is True


async def test_filter_by_days_ago(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="filter-daysago")
    fresh = await _create_published_job(client, employer_token, company_id)
    old = await _create_published_job(
        client, employer_token, company_id, title="Ancient Opening"
    )
    await _backdate_job(old["id"], days=90)

    resp = await client.get(f"{API}/jobs/search", params={"days_ago": 30})
    items = resp.json()["items"]
    assert fresh["id"] in [i["id"] for i in items]
    assert old["id"] not in [i["id"] for i in items]


async def test_filter_by_company_id(client: AsyncClient, employer_token: str) -> None:
    company_a = await _create_company("Company A", "filter-company-a")
    company_b = await _create_company("Company B", "filter-company-b")
    job_a = await _create_published_job(client, employer_token, company_a)
    await _create_published_job(
        client, employer_token, company_b, title="Other Company Role"
    )

    resp = await client.get(f"{API}/jobs/search", params={"company_id": company_a})
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [job_a["id"]]
    assert items[0]["company"]["name"] == "Company A"


async def test_invalid_salary_range_returns_422(client: AsyncClient) -> None:
    resp = await client.get(
        f"{API}/jobs/search", params={"salary_min": 50000, "salary_max": 10000}
    )
    assert resp.status_code == 422


async def test_limit_above_maximum_returns_422(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/jobs/search", params={"limit": 101})
    assert resp.status_code == 422


async def test_page_zero_returns_422(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/jobs/search", params={"page": 0})
    assert resp.status_code == 422


async def test_invalid_sort_by_returns_422(client: AsyncClient) -> None:
    resp = await client.get(f"{API}/jobs/search", params={"sort_by": "hacker"})
    assert resp.status_code == 422


# ── Sorting ──────────────────────────────────────────────────────────


async def test_sort_newest_first(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="sort-newest")
    first = await _create_published_job(
        client, employer_token, company_id, title="First Posted"
    )
    second = await _create_published_job(
        client, employer_token, company_id, title="Second Posted"
    )

    resp = await client.get(
        f"{API}/jobs/search",
        params={"sort_by": "posted_date", "sort_order": "desc"},
    )
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [second["id"], first["id"]]


async def test_sort_oldest_first(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="sort-oldest")
    first = await _create_published_job(
        client, employer_token, company_id, title="First Posted"
    )
    second = await _create_published_job(
        client, employer_token, company_id, title="Second Posted"
    )

    resp = await client.get(
        f"{API}/jobs/search",
        params={"sort_by": "posted_date", "sort_order": "asc"},
    )
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [first["id"], second["id"]]


async def test_sort_salary_high_to_low(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="sort-salary-desc")
    rich = await _create_published_job(
        client,
        employer_token,
        company_id,
        salary_min=40000,
        salary_max=80000,
        title="Rich Role",
    )
    modest = await _create_published_job(
        client,
        employer_token,
        company_id,
        salary_min=5000,
        salary_max=9000,
        title="Modest Role",
    )

    resp = await client.get(
        f"{API}/jobs/search",
        params={"sort_by": "salary_max", "sort_order": "desc"},
    )
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [rich["id"], modest["id"]]


async def test_sort_salary_low_to_high(client: AsyncClient, employer_token: str) -> None:
    company_id = await _create_company(slug="sort-salary-asc")
    rich = await _create_published_job(
        client,
        employer_token,
        company_id,
        salary_min=40000,
        salary_max=80000,
        title="Rich Role",
    )
    modest = await _create_published_job(
        client,
        employer_token,
        company_id,
        salary_min=5000,
        salary_max=9000,
        title="Modest Role",
    )

    resp = await client.get(
        f"{API}/jobs/search",
        params={"sort_by": "salary_min", "sort_order": "asc"},
    )
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [modest["id"], rich["id"]]


async def test_relevance_is_default_only_with_query(
    client: AsyncClient, employer_token: str
) -> None:
    """Without q, default sort falls back to newest-first."""
    company_id = await _create_company(slug="sort-default")
    older = await _create_published_job(
        client, employer_token, company_id, title="Older Job"
    )
    newer = await _create_published_job(
        client, employer_token, company_id, title="Newer Job"
    )

    resp = await client.get(f"{API}/jobs/search")
    items = resp.json()["items"]
    assert [i["id"] for i in items] == [newer["id"], older["id"]]
    # No query => no relevance scoring
    assert all(i["relevance_score"] is None for i in items)


# ── Pagination ───────────────────────────────────────────────────────


async def test_pagination_metadata_and_pages(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="pagination-meta")
    for idx in range(7):
        await _create_published_job(
            client, employer_token, company_id, title=f"Paginated Role {idx}"
        )

    resp = await client.get(f"{API}/jobs/search", params={"page": 1, "limit": 3})
    body = resp.json()
    assert body["total"] == 7
    assert body["page"] == 1
    assert body["limit"] == 3
    assert body["pages"] == 3
    assert body["has_next"] is True
    assert body["has_previous"] is False
    assert len(body["items"]) == 3

    page2 = (await client.get(f"{API}/jobs/search", params={"page": 2, "limit": 3})).json()
    assert page2["has_next"] is True
    assert page2["has_previous"] is True
    assert len(page2["items"]) == 3

    page3 = (await client.get(f"{API}/jobs/search", params={"page": 3, "limit": 3})).json()
    assert page3["has_next"] is False
    assert len(page3["items"]) == 1

    # Page 2 returns different jobs than page 1
    ids_p1 = {i["id"] for i in body["items"]}
    ids_p2 = {i["id"] for i in page2["items"]}
    assert ids_p1.isdisjoint(ids_p2)


async def test_pagination_beyond_last_page_returns_empty(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="pagination-edge")
    await _create_published_job(client, employer_token, company_id)

    resp = await client.get(f"{API}/jobs/search", params={"page": 99})
    body = resp.json()
    assert body["total"] == 1
    assert body["items"] == []
    assert body["has_next"] is False
    assert body["has_previous"] is True


# ── Combined search + filters ────────────────────────────────────────


async def test_search_combined_with_filters_and_pagination(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company(slug="search-combo")
    match = await _create_published_job(
        client,
        employer_token,
        company_id,
        employment_type="contract",
        salary_min=20000,
        salary_max=35000,
        is_remote=True,
        location="Addis Ababa",
    )
    await _create_published_job(
        client,
        employer_token,
        company_id,
        employment_type="full-time",
        title="Software Tester",
    )

    resp = await client.get(
        f"{API}/jobs/search",
        params={
            "q": "software",
            "employment_type": "contract",
            "salary_min": 15000,
            "is_remote": True,
            "location": "addis",
        },
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == match["id"]


# ── Enhanced detail endpoint ─────────────────────────────────────────


async def test_job_detail_includes_company_and_related_jobs(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company("Detail Corp", "detail-corp")
    main = await _create_published_job(client, employer_token, company_id)
    sibling = await _create_published_job(
        client,
        employer_token,
        company_id,
        title="Staff Software Engineer",
    )

    resp = await client.get(f"{API}/jobs/{main['id']}")
    assert resp.status_code == 200
    detail = resp.json()

    # Company information present
    assert detail["company"]["id"] == company_id
    assert detail["company"]["name"] == "Detail Corp"

    # Related jobs include the sibling posting from the same company,
    # but never the job itself.
    related_ids = [j["id"] for j in detail["related_jobs"]]
    assert sibling["id"] in related_ids
    assert main["id"] not in related_ids


async def test_related_jobs_can_be_disabled(
    client: AsyncClient, employer_token: str
) -> None:
    company_id = await _create_company("Detail Corp 2", "detail-corp-2")
    main = await _create_published_job(client, employer_token, company_id)

    resp = await client.get(f"{API}/jobs/{main['id']}", params={"include_related": False})
    assert resp.status_code == 200
    assert resp.json()["related_jobs"] == []


# ── Performance ──────────────────────────────────────────────────────


async def test_search_executes_within_budget(
    client: AsyncClient, employer_token: str
) -> None:
    """Typical search must complete well under the 500ms budget."""
    company_id = await _create_company(slug="perf-check")
    for idx in range(10):
        await _create_published_job(
            client, employer_token, company_id, title=f"Software Engineer {idx}"
        )

    start = time.perf_counter()
    resp = await client.get(
        f"{API}/jobs/search",
        params={"q": "software engineer", "limit": 20},
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert resp.status_code == 200
    assert resp.json()["total"] == 10
    # Generous bound to avoid CI flakiness while catching regressions.
    assert elapsed_ms < 500, f"search took {elapsed_ms:.1f}ms"
