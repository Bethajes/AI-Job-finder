"""Week 7: device-token and notification-preferences endpoint tests."""

import json
import logging

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.config import settings

API = settings.API_V1_PREFIX

SEEKER = {
    "email": "notif-seeker@example.com",
    "first_name": "Alice",
    "last_name": "Notif",
    "password": "securepassword123",
    "role": "job_seeker",
}

EMPLOYER = {
    "email": "notif-employer@example.com",
    "first_name": "Bob",
    "last_name": "Employer",
    "password": "securepassword123",
    "role": "employer",
}

FAKE_PDF = b"%PDF-1.4\n%fake pdf content for testing\n"


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


@pytest.fixture(autouse=True)
async def cleanup():
    await _cleanup()
    yield
    await _cleanup()


# ── Device tokens ───────────────────────────────────────────────────────


async def test_register_device_token_returns_201(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "fcm-token-abc-123", "device_type": "android"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["message"] == "Device token registered"
    assert data["device_type"] == "android"


async def test_register_device_token_ios(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "fcm-token-ios-456", "device_type": "ios"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["device_type"] == "ios"


async def test_register_device_token_web(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "fcm-token-web-789", "device_type": "web"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["device_type"] == "web"


async def test_register_duplicate_token_updates(client: AsyncClient):
    """Re-registering the same token should update (not duplicate)."""
    token = await _register(client, SEEKER)
    resp1 = await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "fcm-token-dup", "device_type": "android"},
    )
    assert resp1.status_code == 201

    resp2 = await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "fcm-token-dup", "device_type": "ios"},
    )
    assert resp2.status_code == 201
    # Device type should be updated
    assert resp2.json()["device_type"] == "ios"
    assert resp2.json()["id"] == resp1.json()["id"]


async def test_register_invalid_device_type_returns_422(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "fcm-token-bad", "device_type": "windows_phone"},
    )
    assert resp.status_code == 422, resp.text


async def test_register_empty_token_returns_422(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "", "device_type": "android"},
    )
    assert resp.status_code == 422


async def test_remove_device_token_returns_200(client: AsyncClient):
    token = await _register(client, SEEKER)
    # Register first
    await client.post(
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        json={"device_token": "fcm-token-to-remove", "device_type": "android"},
    )

    resp = await client.request(
        "DELETE",
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        content=json.dumps({"device_token": "fcm-token-to-remove"}),
    )
    assert resp.status_code == 200, resp.text
    assert "removed" in resp.json()["message"].lower()


async def test_remove_nonexistent_token_returns_200_gracefully(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.request(
        "DELETE",
        f"{API}/device-tokens",
        headers=await _auth_headers(token),
        content=json.dumps({"device_token": "never-registered-token"}),
    )
    assert resp.status_code == 200, resp.text
    assert "not found" in resp.json()["message"].lower()


async def test_device_token_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.post(
        f"{API}/device-tokens",
        json={"device_token": "fcm-token-noauth", "device_type": "android"},
    )
    assert resp.status_code == 401


# ── Notification preferences ────────────────────────────────────────────


async def test_get_notification_preferences_returns_defaults(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.get(
        f"{API}/users/me/notification-preferences",
        headers=await _auth_headers(token),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["application_updates"] is True
    assert data["new_jobs"] is True
    assert data["marketing"] is False
    assert data["in_app"] is True


async def test_update_notification_preferences(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.put(
        f"{API}/users/me/notification-preferences",
        headers=await _auth_headers(token),
        json={"marketing": True, "application_updates": False},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["marketing"] is True
    assert data["application_updates"] is False
    # Defaults preserved for non-updated fields
    assert data["new_jobs"] is True
    assert data["in_app"] is True


async def test_update_preferences_partial_persists(client: AsyncClient):
    token = await _register(client, SEEKER)

    # Update once
    await client.put(
        f"{API}/users/me/notification-preferences",
        headers=await _auth_headers(token),
        json={"marketing": True},
    )

    # Update again (different field)
    resp = await client.put(
        f"{API}/users/me/notification-preferences",
        headers=await _auth_headers(token),
        json={"new_jobs": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    # First update should be persisted
    assert data["marketing"] is True
    assert data["new_jobs"] is False
    assert data["in_app"] is True


async def test_get_preferences_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get(f"{API}/users/me/notification-preferences")
    assert resp.status_code == 401


async def test_update_preferences_invalid_field_returns_422(client: AsyncClient):
    token = await _register(client, SEEKER)
    resp = await client.put(
        f"{API}/users/me/notification-preferences",
        headers=await _auth_headers(token),
        json={"totally_invalid": True},
    )
    assert resp.status_code == 422


# ── Application triggers push notification (graceful when FCM off) ──────


async def test_apply_triggers_push_task_without_error(client: AsyncClient, caplog):
    """Application submission should schedule a push notification background task.
    Since FCM is not configured in tests, it should silently no-op."""
    employer_token = await _register(client, EMPLOYER)
    seeker_token = await _register(client, SEEKER)

    from app.core.database import AsyncSessionLocal
    from app.models.company import Company
    from app.models.user import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == EMPLOYER["email"]))
        user = result.scalar_one()
        company = Company(owner_id=user.id, name="TechCo", slug="techco")
        db.add(company)
        await db.commit()
        await db.refresh(company)
        company_id = str(company.id)

    # Create and publish job
    resp = await client.post(
        f"{API}/jobs",
        headers=await _auth_headers(employer_token),
        json={
            "title": "Backend Dev",
            "description": "Build APIs",
            "company_id": company_id,
            "employment_type": "full-time",
            "experience_level": "mid",
            "location": "Addis Ababa",
        },
    )
    assert resp.status_code == 201
    job = resp.json()

    resp = await client.patch(
        f"{API}/jobs/{job['id']}/publish",
        headers=await _auth_headers(employer_token),
    )
    assert resp.status_code == 200

    # Apply
    files = {"resume": ("resume.pdf", FAKE_PDF, "application/pdf")}
    data = {"job_id": job["id"]}

    with caplog.at_level(logging.WARNING, logger="app.core.fcm"):
        resp = await client.post(
            f"{API}/applications",
            headers=await _auth_headers(seeker_token),
            data=data,
            files=files,
        )
        assert resp.status_code == 201, resp.text
