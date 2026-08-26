"""Week 6: job application flow tests."""

import uuid
import logging

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

from app.core.config import settings

API = settings.API_V1_PREFIX

SEEKER_A = {
    "email": "apps-seeker-a@example.com",
    "first_name": "Alice",
    "last_name": "Seeker",
    "password": "securepassword123",
    "role": "job_seeker",
}
SEEKER_B = {
    "email": "apps-seeker-b@example.com",
    "first_name": "Bob",
    "last_name": "Seeker",
    "password": "securepassword123",
    "role": "job_seeker",
}
EMPLOYER_A = {
    "email": "apps-employer-a@example.com",
    "first_name": "Alpha",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}
EMPLOYER_B = {
    "email": "apps-employer-b@example.com",
    "first_name": "Beta",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}

FAKE_PDF = b"%PDF-1.4\n%fake pdf content for testing\n"
FAKE_DOCX = b"PK\x03\x04 fake docx zip bytes"


def _future_deadline(days: int = 30) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _job_payload(company_id: str, **overrides) -> dict:
    payload = {
        "title": "Backend Developer",
        "description": "We are looking for a backend developer to join us.",
        "company_id": company_id,
        "employment_type": "full-time",
        "experience_level": "mid",
        "location": "Addis Ababa",
        "application_deadline": _future_deadline(),
    }
    payload.update(overrides)
    return payload


async def _cleanup() -> None:
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
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
        result = await db.execute(select(User).where(User.email == owner_email))
        user = result.scalar_one()
        company = Company(owner_id=user.id, name=name, slug=slug)
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return str(company.id)


async def _create_published_job(
    client: AsyncClient, token: str, company_id: str, **overrides
) -> dict:
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(token),
        json=_job_payload(company_id, **overrides),
    )
    assert resp.status_code == 201, resp.text
    job = resp.json()
    resp = await client.patch(
        f"{API}/jobs/{job['id']}/publish",
        headers=await _auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _apply(
    client: AsyncClient,
    token: str,
    job_id: str,
    *,
    filename: str = "resume.pdf",
    content: bytes = FAKE_PDF,
    content_type: str = "application/pdf",
    cover_letter: str | None = "I am excited to apply.",
):
    files = {"resume": (filename, content, content_type)}
    data: dict = {"job_id": job_id}
    if cover_letter is not None:
        data["cover_letter"] = cover_letter
    return await client.post(
        f"{API}/applications",
        headers=await _auth_headers(token),
        data=data,
        files=files,
    )


@pytest.fixture(autouse=True)
async def cleanup(tmp_path, monkeypatch):
    # Local storage fallback target so uploads never touch the real dir.
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    await _cleanup()
    yield
    await _cleanup()


# ── Submission ───────────────────────────────────────────────────────


async def test_apply_to_job_returns_201_with_application_id(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-apps")
    job = await _create_published_job(client, employer_token, company_id)

    resp = await _apply(client, seeker_token, job["id"])

    assert resp.status_code == 201, resp.text
    body = resp.json()
    application_id = uuid.UUID(body["id"])
    assert body["status"] == "applied"
    assert body["cover_letter"] == "I am excited to apply."
    assert body["resume_url"]
    assert body["message"] == "Application submitted successfully"
    assert "employer_notes" not in body

    # applications_count incremented on the job
    resp = await client.get(f"{API}/jobs/{job['id']}")
    assert resp.json()["applications_count"] == 1


async def test_apply_to_same_job_twice_returns_409(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-dup")
    job = await _create_published_job(client, employer_token, company_id)

    first = await _apply(client, seeker_token, job["id"])
    assert first.status_code == 201

    second = await _apply(client, seeker_token, job["id"])
    assert second.status_code == 409


async def test_reapply_allowed_after_rejection(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-re")
    job = await _create_published_job(client, employer_token, company_id)

    first = await _apply(client, seeker_token, job["id"])
    application_id = first.json()["id"]

    resp = await client.patch(
        f"{API}/applications/{application_id}/status",
        headers=await _auth_headers(employer_token),
        json={"status": "rejected"},
    )
    assert resp.status_code == 200

    reapply = await _apply(client, seeker_token, job["id"])
    assert reapply.status_code == 201
    assert reapply.json()["id"] != application_id


async def test_apply_as_employer_returns_403(client: AsyncClient):
    employer_token = await _register(client, EMPLOYER_A)
    other_employer_token = await _register(client, EMPLOYER_B)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-403")
    job = await _create_published_job(client, employer_token, company_id)

    resp = await _apply(client, other_employer_token, job["id"])
    assert resp.status_code == 403


async def test_apply_with_invalid_file_type_returns_400(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-file")
    job = await _create_published_job(client, employer_token, company_id)

    resp = await _apply(
        client,
        seeker_token,
        job["id"],
        filename="notes.txt",
        content=b"just text",
        content_type="text/plain",
    )
    assert resp.status_code == 400


async def test_apply_with_oversized_resume_returns_400(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-big")
    job = await _create_published_job(client, employer_token, company_id)

    big_pdf = b"%PDF-1.4" + b"\0" * (5 * 1024 * 1024)
    resp = await _apply(client, seeker_token, job["id"], content=big_pdf)
    assert resp.status_code == 400


async def test_apply_with_docx_resume_succeeds(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-docx")
    job = await _create_published_job(client, employer_token, company_id)

    resp = await _apply(
        client,
        seeker_token,
        job["id"],
        filename="resume.docx",
        content=FAKE_DOCX,
        content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    )
    assert resp.status_code == 201, resp.text


async def test_apply_to_draft_job_returns_400(client: AsyncClient):
    seeker_token = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-draft")
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(employer_token),
        json=_job_payload(company_id),
    )
    draft_job = resp.json()

    resp = await _apply(client, seeker_token, draft_job["id"])
    assert resp.status_code == 400


async def test_apply_without_auth_returns_401(client: AsyncClient):
    resp = await client.post(
        f"{API}/applications",
        data={"job_id": str(uuid.uuid4())},
        files={"resume": ("resume.pdf", FAKE_PDF, "application/pdf")},
    )
    assert resp.status_code == 401


# ── Listings ─────────────────────────────────────────────────────────


async def test_seeker_list_shows_only_own_applications(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    token_b = await _register(client, SEEKER_B)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-list")
    job_a = await _create_published_job(client, employer_token, company_id)
    job_b = await _create_published_job(
        client, employer_token, company_id, title="Frontend Developer"
    )

    await _apply(client, token_a, job_a["id"])
    await _apply(client, token_a, job_b["id"])
    await _apply(client, token_b, job_a["id"])

    resp = await client.get(
        f"{API}/applications/me", headers=await _auth_headers(token_a)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(item["applicant"]["email"] == SEEKER_A["email"] for item in body["items"])
    titles = {item["job"]["title"] for item in body["items"]}
    assert titles == {"Backend Developer", "Frontend Developer"}

    resp_b = await client.get(
        f"{API}/applications/me", headers=await _auth_headers(token_b)
    )
    assert resp_b.json()["total"] == 1


async def test_seeker_list_filters_by_status_and_title(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-filt")
    dev_job = await _create_published_job(client, employer_token, company_id)
    ops_job = await _create_published_job(
        client, employer_token, company_id, title="DevOps Engineer"
    )

    dev_application = (await _apply(client, token_a, dev_job["id"])).json()["id"]
    await _apply(client, token_a, ops_job["id"])

    await client.patch(
        f"{API}/applications/{dev_application}/status",
        headers=await _auth_headers(employer_token),
        json={"status": "viewed"},
    )

    resp = await client.get(
        f"{API}/applications/me",
        params={"status": "viewed"},
        headers=await _auth_headers(token_a),
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["job"]["title"] == "Backend Developer"

    resp = await client.get(
        f"{API}/applications/me",
        params={"job_title": "devops"},
        headers=await _auth_headers(token_a),
    )
    assert resp.json()["total"] == 1


async def test_employer_list_shows_only_their_jobs_applications(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    employer_a = await _register(client, EMPLOYER_A)
    employer_b = await _register(client, EMPLOYER_B)
    company_a = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-pipe")
    company_b = await _create_company(EMPLOYER_B["email"], "Beta Corp", "beta-pipe")
    job_a = await _create_published_job(client, employer_a, company_a)
    job_b = await _create_published_job(client, employer_b, company_b)

    await _apply(client, token_a, job_a["id"])
    await _apply(client, token_a, job_b["id"])

    resp = await client.get(
        f"{API}/applications/company", headers=await _auth_headers(employer_a)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    applicant_view = body["items"][0]
    assert applicant_view["applicant"]["email"] == SEEKER_A["email"]
    assert applicant_view["applicant"]["full_name"] == "Alice Seeker"
    assert applicant_view["job"]["title"] == "Backend Developer"
    assert "employer_notes" in applicant_view


async def test_employer_list_filter_by_job_and_status_sort(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-sort")
    job_1 = await _create_published_job(client, employer_token, company_id)
    job_2 = await _create_published_job(
        client, employer_token, company_id, title="QA Engineer"
    )

    for job in (job_1, job_2):
        await _apply(client, token_a, job["id"])

    resp = await client.get(
        f"{API}/applications/company",
        params={"job_id": job_2["id"]},
        headers=await _auth_headers(employer_token),
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["job_id"] == job_2["id"]

    resp = await client.get(
        f"{API}/applications/company",
        params={"status": "applied", "sort_by": "status", "sort_order": "asc"},
        headers=await _auth_headers(employer_token),
    )
    assert resp.json()["total"] == 2


# ── Status management ────────────────────────────────────────────────


async def test_update_status_pipeline_notifies_applicant(
    client: AsyncClient, caplog
):
    token_a = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-flow")
    job = await _create_published_job(client, employer_token, company_id)
    application_id = (await _apply(client, token_a, job["id"])).json()["id"]

    with caplog.at_level(logging.INFO, logger="app.services.email_service"):
        pipeline = ["viewed", "shortlisted", "interviewed", "offered", "hired"]
        seen_notes = None
        for index, status_value in enumerate(pipeline):
            payload: dict = {"status": status_value}
            if status_value == "interviewed":
                from datetime import datetime, timedelta, timezone

                payload["interview_date"] = (
                    datetime.now(timezone.utc) + timedelta(days=7)
                ).isoformat()
            if status_value == "shortlisted":
                seen_notes = "Strong Python background."
                payload["employer_notes"] = seen_notes

            resp = await client.patch(
                f"{API}/applications/{application_id}/status",
                headers=await _auth_headers(employer_token),
                json=payload,
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["status"] == status_value
            if status_value == "viewed":
                assert data["viewed_at"] is not None
            if status_value == "shortlisted":
                assert data["employer_notes"] == seen_notes
            if status_value == "interviewed":
                assert data["interview_date"] is not None

        # Applicant got one notification per transition.
        update_emails = [
            record for record in caplog.records
            if "Update on your application" in record.getMessage()
        ]
        assert len(update_emails) >= len(pipeline)


async def test_invalid_status_transition_returns_400(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-inv")
    job = await _create_published_job(client, employer_token, company_id)
    application_id = (await _apply(client, token_a, job["id"])).json()["id"]

    resp = await client.patch(
        f"{API}/applications/{application_id}/status",
        headers=await _auth_headers(employer_token),
        json={"status": "hired"},
    )
    assert resp.status_code == 400

    resp = await client.patch(
        f"{API}/applications/{application_id}/status",
        headers=await _auth_headers(employer_token),
        json={"status": "applied"},
    )
    assert resp.status_code == 400


async def test_update_status_requires_owning_employer(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    other_employer = await _register(client, EMPLOYER_B)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-own")
    job = await _create_published_job(client, employer_token, company_id)
    application_id = (await _apply(client, token_a, job["id"])).json()["id"]

    resp = await client.patch(
        f"{API}/applications/{application_id}/status",
        headers=await _auth_headers(other_employer),
        json={"status": "viewed"},
    )
    assert resp.status_code == 404


# ── Detail & permissions ─────────────────────────────────────────────


async def test_detail_permissions_between_roles(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    other_employer = await _register(client, EMPLOYER_B)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-det")
    job = await _create_published_job(client, employer_token, company_id)
    application_id = (await _apply(client, token_a, job["id"])).json()["id"]

    await client.patch(
        f"{API}/applications/{application_id}/status",
        headers=await _auth_headers(employer_token),
        json={"status": "viewed", "employer_notes": "Private note."},
    )

    # Seeker: no employer_notes field at all.
    resp = await client.get(
        f"{API}/applications/{application_id}",
        headers=await _auth_headers(token_a),
    )
    assert resp.status_code == 200
    seeker_view = resp.json()
    assert "employer_notes" not in seeker_view
    assert seeker_view["job"]["company_name"] == "Alpha Corp"

    # Owning employer: sees notes and analytics metadata.
    resp = await client.get(
        f"{API}/applications/{application_id}",
        headers=await _auth_headers(employer_token),
    )
    assert resp.status_code == 200
    employer_view = resp.json()
    assert employer_view["employer_notes"] == "Private note."
    assert employer_view["ip_address"] is not None

    # Another employer cannot see it at all.
    resp = await client.get(
        f"{API}/applications/{application_id}",
        headers=await _auth_headers(other_employer),
    )
    assert resp.status_code == 404

    # Unauthenticated gets 401.
    resp = await client.get(f"{API}/applications/{application_id}")
    assert resp.status_code == 401


# ── Withdrawal / re-application ──────────────────────────────────────


async def test_withdraw_then_reapply(client: AsyncClient):
    token_a = await _register(client, SEEKER_A)
    employer_token = await _register(client, EMPLOYER_A)
    company_id = await _create_company(EMPLOYER_A["email"], "Alpha Corp", "alpha-wd")
    job = await _create_published_job(client, employer_token, company_id)
    application_id = (await _apply(client, token_a, job["id"])).json()["id"]

    resp = await client.patch(
        f"{API}/applications/{application_id}/withdraw",
        headers=await _auth_headers(token_a),
        json={"reason": "Accepted another offer"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "withdrawn"

    # Employer cannot withdraw on the applicant's behalf.
    second = await _apply(client, token_a, job["id"])
    assert second.status_code == 201
    second_id = second.json()["id"]

    resp = await client.patch(
        f"{API}/applications/{second_id}/withdraw",
        headers=await _auth_headers(employer_token),
    )
    assert resp.status_code == 404
