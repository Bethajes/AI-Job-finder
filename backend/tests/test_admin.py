"""Week 8: admin dashboard & management system tests."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.config import settings

API = settings.API_V1_PREFIX

ADMIN = {
    "email": "admin@example.com",
    "first_name": "Ada",
    "last_name": "Admin",
    "password": "securepassword123",
    "role": "job_seeker",  # promoted below, like real ops would
}
SEEKER_A = {
    "email": "admin-seeker-a@example.com",
    "first_name": "Alice",
    "last_name": "Seeker",
    "password": "securepassword123",
    "role": "job_seeker",
}
SEEKER_B = {
    "email": "admin-seeker-b@example.com",
    "first_name": "Bob",
    "last_name": "Seeker",
    "password": "securepassword123",
    "role": "job_seeker",
}
EMPLOYER = {
    "email": "admin-employer@example.com",
    "first_name": "Eddy",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}


def _future_deadline(days: int = 30) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


async def _cleanup() -> None:
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        for table in (
            "admin_logs",
            "saved_jobs",
            "device_tokens",
            "applications",
            "jobs",
            "companies",
            "job_seeker_profiles",
            "users",
        ):
            await db.execute(text(f"DELETE FROM {table}"))
        await db.commit()


async def _register(client: AsyncClient, payload: dict) -> str:
    resp = await client.post(f"{API}/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


async def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _promote_to_admin(email: str) -> None:
    """Promote an existing user to admin directly in the DB."""
    from app.core.database import AsyncSessionLocal
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = "admin"
        user.is_active = True
        await db.commit()


async def _create_company(owner_email: str, name: str, slug: str) -> str:
    from app.core.database import AsyncSessionLocal
    from app.models.company import Company
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.email == owner_email))
        ).scalar_one()
        company = Company(owner_id=user.id, name=name, slug=slug)
        db.add(company)
        await db.commit()
        return str(company.id)


async def _create_published_job(
    client: AsyncClient, token: str, company_id: str, **overrides
) -> dict:
    payload = {
        "title": overrides.pop("title", "Backend Developer"),
        "description": "Great role at a great company.",
        "company_id": company_id,
        "employment_type": "full-time",
        "experience_level": "mid",
        "location": "Addis Ababa",
        "application_deadline": _future_deadline(),
        **overrides,
    }
    resp = await client.post(
        f"{API}/jobs", headers=await _headers(token), json=payload
    )
    assert resp.status_code == 201, resp.text
    job = resp.json()
    resp = await client.patch(
        f"{API}/jobs/{job['id']}/publish", headers=await _headers(token)
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(autouse=True)
async def cleanup():
    await _cleanup()
    yield
    await _cleanup()


# ── Access control ───────────────────────────────────────────────────


async def test_non_admin_cannot_access_admin_endpoints(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)

    for method, path in (
        ("GET", f"{API}/admin/users"),
        ("PATCH", f"{API}/admin/users/{uuid.uuid4()}"),
        ("DELETE", f"{API}/admin/users/{uuid.uuid4()}"),
        ("POST", f"{API}/admin/users/{uuid.uuid4()}/verify"),
        ("GET", f"{API}/admin/companies"),
        ("PATCH", f"{API}/admin/companies/{uuid.uuid4()}/verify"),
        ("GET", f"{API}/admin/jobs"),
        ("PATCH", f"{API}/admin/jobs/{uuid.uuid4()}/moderate"),
        ("GET", f"{API}/admin/stats"),
        ("GET", f"{API}/admin/audit-logs"),
    ):
        resp = await client.request(
            method, path, headers=await _headers(seeker_token), json={}
        )
        assert resp.status_code == 403, f"{method} {path}: {resp.text}"
        assert resp.json()["detail"] == "Admin access required"

    # Unauthenticated too
    resp = await client.get(f"{API}/admin/users")
    assert resp.status_code == 401


# ── User management ──────────────────────────────────────────────────


async def test_admin_can_list_filter_and_search_users(client: AsyncClient):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)

    await _register(client, SEEKER_A)
    await _register(client, EMPLOYER)

    resp = await client.get(f"{API}/admin/users", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 3
    emails = {u["email"] for u in body["items"]}
    assert ADMIN["email"] in emails and SEEKER_A["email"] in emails
    # Password hash never leaks
    assert all("hashed_password" not in u for u in body["items"])

    # Role filter
    resp = await client.get(
        f"{API}/admin/users", headers=headers, params={"role": "employer"}
    )
    assert resp.status_code == 200
    assert {u["role"] for u in resp.json()["items"]} == {"employer"}

    # Search by name fragment
    resp = await client.get(
        f"{API}/admin/users", headers=headers, params={"search": "Alice"}
    )
    assert [u["first_name"] for u in resp.json()["items"]] == ["Alice"]

    # Sort by last_login asc puts never-logged-in... all logged in; stable check
    resp = await client.get(
        f"{API}/admin/users",
        headers=headers,
        params={"sort_by": "created_at", "sort_order": "asc"},
    )
    created = [u["created_at"] for u in resp.json()["items"]]
    assert created == sorted(created)


async def test_admin_gets_user_detail_with_stats(client: AsyncClient):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)

    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Acme ET", "acme-et-admin")
    job = await _create_published_job(client, employer_token, company_id)

    files = {"resume": ("r.pdf", b"%PDF-fake", "application/pdf")}
    resp = await client.post(
        f"{API}/applications",
        headers=await _headers(seeker_token),
        data={"job_id": job["id"]},
        files=files,
    )
    assert resp.status_code == 201, resp.text

    # Seeker detail includes application stats
    seeker_id = str((await client.get(f"{API}/auth/me", headers=await _headers(seeker_token))).json()["id"])
    resp = await client.get(f"{API}/admin/users/{seeker_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["application_stats"]["total"] == 1
    assert detail["application_stats"]["by_status"]["applied"] == 1

    # Employer detail includes job stats
    employer_id = str((await client.get(f"{API}/auth/me", headers=await _headers(employer_token))).json()["id"])
    resp = await client.get(f"{API}/admin/users/{employer_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["job_stats"]["total_jobs"] == 1
    assert resp.json()["job_stats"]["total_applications_received"] == 1


async def test_admin_cannot_change_own_role_or_delete_self(client: AsyncClient):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)
    admin_id = str(
        (await client.get(f"{API}/auth/me", headers=headers)).json()["id"]
    )

    resp = await client.patch(
        f"{API}/admin/users/{admin_id}",
        headers=headers,
        json={"role": "job_seeker"},
    )
    assert resp.status_code == 400

    resp = await client.patch(
        f"{API}/admin/users/{admin_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert resp.status_code == 400

    resp = await client.delete(f"{API}/admin/users/{admin_id}", headers=headers)
    assert resp.status_code == 400


async def test_admin_update_soft_delete_and_verify_user(client: AsyncClient):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)

    victim_token = await _register(client, SEEKER_A)
    victim_id = str(
        (await client.get(f"{API}/auth/me", headers=await _headers(victim_token))).json()["id"]
    )

    # Update role
    resp = await client.patch(
        f"{API}/admin/users/{victim_id}", headers=headers, json={"role": "employer"}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "employer"

    # Manual email verification override
    resp = await client.post(f"{API}/admin/users/{victim_id}/verify", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_verified"] is True

    # Soft delete deactivates
    resp = await client.delete(f"{API}/admin/users/{victim_id}", headers=headers)
    assert resp.status_code == 200
    resp = await client.get(f"{API}/admin/users/{victim_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Hard delete removes entirely
    disposable = {**SEEKER_B, "email": "admin-disposable@example.com"}
    d_token = await _register(client, disposable)
    d_id = str((await client.get(f"{API}/auth/me", headers=await _headers(d_token))).json()["id"])
    resp = await client.delete(
        f"{API}/admin/users/{d_id}", headers=headers, params={"hard": True}
    )
    assert resp.status_code == 200
    resp = await client.get(f"{API}/admin/users/{d_id}", headers=headers)
    assert resp.status_code == 404


# ── Company approval ─────────────────────────────────────────────────


async def test_admin_can_list_and_verify_companies_and_owner_notified(
    client: AsyncClient, monkeypatch
):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)

    await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "Verify Me PLC", "verify-me")

    # Capture the owner-notification background task.
    sent: list[dict] = []

    async def fake_email(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr(
        "app.api.v1.endpoints.admin_companies.send_company_verification_email",
        fake_email,
    )

    # Pending appears in pending filter
    resp = await client.get(
        f"{API}/admin/companies",
        headers=headers,
        params={"verification_status": "pending"},
    )
    assert resp.status_code == 200
    assert any(c["id"] == company_id for c in resp.json()["items"])

    # Approve
    resp = await client.patch(
        f"{API}/admin/companies/{company_id}/verify",
        headers=headers,
        json={"status": "approved", "admin_notes": "Documents check out"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verification_status"] == "approved"
    assert body["is_verified"] is True
    assert body["admin_notes"] == "Documents check out"
    assert body["verified_at"] is not None

    # Owner notified
    assert len(sent) == 1
    assert sent[0]["owner_email"] == EMPLOYER["email"]
    assert sent[0]["status"] == "approved"

    # Reject flow keeps is_verified False
    resp = await client.patch(
        f"{API}/admin/companies/{company_id}/verify",
        headers=headers,
        json={"status": "rejected", "admin_notes": "Invalid license"},
    )
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "rejected"
    assert resp.json()["is_verified"] is False
    assert len(sent) == 2

    # Company detail aggregates jobs/applications
    resp = await client.get(f"{API}/admin/companies/{company_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["owner"]["email"] == EMPLOYER["email"]
    assert detail["job_count"] == 0


# ── Job moderation ───────────────────────────────────────────────────


async def test_admin_can_moderate_jobs_flag_hide_and_public_visibility(
    client: AsyncClient,
):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    admin_headers = await _headers(admin_token)

    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "ModCo", "modco")
    job = await _create_published_job(client, employer_token, company_id)
    job_id = job["id"]

    # Flag for review
    resp = await client.patch(
        f"{API}/admin/jobs/{job_id}/moderate",
        headers=admin_headers,
        json={"action": "flag", "admin_notes": "Suspicious salary"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_flagged"] is True

    resp = await client.get(
        f"{API}/admin/jobs", headers=admin_headers, params={"flagged_only": True}
    )
    assert any(j["id"] == job_id for j in resp.json()["items"])

    # Hide -> disappears from public listings/search
    resp = await client.patch(
        f"{API}/admin/jobs/{job_id}/moderate",
        headers=admin_headers,
        json={"action": "hide"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_hidden"] is True

    resp = await client.get(f"{API}/jobs", headers=admin_headers)
    assert resp.status_code == 200
    assert all(j["id"] != job_id for j in resp.json()["items"])

    resp = await client.get(
        f"{API}/jobs/search", headers=admin_headers, params={"q": "Backend"}
    )
    if resp.status_code == 200:
        assert all(j["id"] != job_id for j in resp.json()["items"])

    # Approve clears flag and restores publication
    resp = await client.patch(
        f"{API}/admin/jobs/{job_id}/moderate",
        headers=admin_headers,
        json={"action": "approve", "admin_notes": "Cleared by review team"},
    )
    assert resp.status_code == 200
    moderated = resp.json()
    assert moderated["status"] == "published"
    assert moderated["is_flagged"] is False
    assert moderated["is_hidden"] is False
    assert moderated["admin_notes"] == "Cleared by review team"

    # Detail shows application stats
    resp = await client.get(f"{API}/admin/jobs/{job_id}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["application_stats"]["total"] == 0

    # Reject closes it
    resp = await client.patch(
        f"{API}/admin/jobs/{job_id}/moderate",
        headers=admin_headers,
        json={"action": "reject", "admin_notes": "Prohibited content"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


# ── Audit logging ────────────────────────────────────────────────────


async def test_all_admin_actions_logged_with_details(client: AsyncClient):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)

    victim_token = await _register(client, SEEKER_A)
    victim_id = str(
        (await client.get(f"{API}/auth/me", headers=await _headers(victim_token))).json()["id"]
    )

    await client.patch(
        f"{API}/admin/users/{victim_id}", headers=headers, json={"role": "employer"}
    )
    await client.post(f"{API}/admin/users/{victim_id}/verify", headers=headers)
    await client.delete(f"{API}/admin/users/{victim_id}", headers=headers)

    resp = await client.get(f"{API}/admin/audit-logs", headers=headers)
    assert resp.status_code == 200
    logs = resp.json()
    actions = {entry["action_type"] for entry in logs["items"]}
    assert {"user_update", "user_verify", "user_delete"} <= actions

    update_entry = next(e for e in logs["items"] if e["action_type"] == "user_update")
    assert update_entry["resource_type"] == "user"
    assert update_entry["resource_id"] == victim_id
    assert update_entry["changes"]["role"] == ["job_seeker", "employer"]
    assert update_entry["admin_email"] == ADMIN["email"]

    # Filter by action type
    resp = await client.get(
        f"{API}/admin/audit-logs", headers=headers, params={"action_type": "user_verify"}
    )
    assert {e["action_type"] for e in resp.json()["items"]} == {"user_verify"}


# ── Dashboard stats & reports ────────────────────────────────────────


async def test_dashboard_stats_reflect_platform_data(client: AsyncClient):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)

    await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "StatsCo", "statsco")
    job = await _create_published_job(
        client, employer_token, company_id, title="Data Analyst", category="Analytics"
    )

    token_a = await _register(client, SEEKER_B)
    files = {"resume": ("r.pdf", b"%PDF-fake", "application/pdf")}
    resp = await client.post(
        f"{API}/applications",
        headers=await _headers(token_a),
        data={"job_id": job["id"]},
        files=files,
    )
    assert resp.status_code == 201

    resp = await client.get(f"{API}/admin/stats", headers=headers)
    assert resp.status_code == 200, resp.text
    stats = resp.json()
    assert stats["total_users"] >= 4
    assert stats["users_by_role"].get("job_seeker", 0) >= 2
    assert stats["users_by_role"].get("admin", 0) >= 1
    assert stats["total_jobs"] >= 1
    assert stats["jobs_by_status"].get("published", 0) >= 1
    assert stats["total_applications"] >= 1
    assert stats["applications_by_status"].get("applied", 0) >= 1
    assert stats["total_companies"] >= 1
    assert stats["new_users_7d"] >= 4
    assert "generated_at" in stats

    # Cached second call stays consistent
    resp2 = await client.get(f"{API}/admin/stats", headers=headers)
    assert resp2.json()["total_users"] == stats["total_users"]

    # User growth/distribution
    resp = await client.get(f"{API}/admin/stats/users", headers=headers)
    assert resp.status_code == 200
    user_stats = resp.json()
    assert len(user_stats["growth_daily"]) == 31
    assert sum(p["count"] for p in user_stats["growth_daily"]) >= 4
    assert user_stats["distribution_by_role"].get("job_seeker", 0) >= 2

    # Job trends
    resp = await client.get(f"{API}/admin/stats/jobs", headers=headers)
    assert resp.status_code == 200
    job_stats = resp.json()
    assert job_stats["average_applications_per_job"] >= 0.5
    assert any(c["category"] == "Analytics" for c in job_stats["popular_categories"])


async def test_reports_return_engagement_and_performance_metrics(
    client: AsyncClient,
):
    admin_token = await _register(client, ADMIN)
    await _promote_to_admin(ADMIN["email"])
    headers = await _headers(admin_token)

    employer_token = await _register(client, EMPLOYER)
    company_id = await _create_company(EMPLOYER["email"], "ReportCo", "reportco")
    job = await _create_published_job(
        client, employer_token, company_id, category="Tech"
    )
    seeker_token = await _register(client, SEEKER_A)
    files = {"resume": ("r.pdf", b"%PDF-fake", "application/pdf")}
    await client.post(
        f"{API}/applications",
        headers=await _headers(seeker_token),
        data={"job_id": job["id"]},
        files=files,
    )

    resp = await client.get(f"{API}/admin/reports/user-activity", headers=headers)
    assert resp.status_code == 200
    activity = resp.json()
    assert "active_users_daily" in activity
    assert "active_users_weekly" in activity
    assert "active_users_monthly" in activity
    assert activity["most_active_users"][0]["email"] == SEEKER_A["email"]
    assert activity["most_active_users"][0]["activity_count"] == 1

    resp = await client.get(f"{API}/admin/reports/job-performance", headers=headers)
    assert resp.status_code == 200
    perf = resp.json()
    assert perf["top_jobs_by_applications"][0]["title"] == "Backend Developer"
    assert perf["top_jobs_by_applications"][0]["applications_count"] == 1
    assert perf["average_applications_per_job"] >= 1.0
    assert perf["jobs_by_employment_type"].get("full-time") == 1
