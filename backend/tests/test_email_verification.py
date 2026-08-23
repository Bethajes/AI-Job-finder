import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    EMAIL_VERIFICATION_TOKEN_TYPE,
)

API = settings.API_V1_PREFIX

REGISTER_PAYLOAD = {
    "email": "verify-test@example.com",
    "first_name": "Verify",
    "last_name": "Tester",
    "password": "securepassword123",
    "role": "job_seeker",
}


async def _cleanup():
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM companies"))
        await db.execute(text("DELETE FROM job_seeker_profiles"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()


async def _register(client: AsyncClient) -> str:
    resp = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    return resp.json()["access_token"]


async def _get_user_id(client: AsyncClient, token: str) -> str:
    resp = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()["id"]


async def _get_user_email(client: AsyncClient, token: str) -> str:
    resp = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()["email"]


@pytest.fixture(autouse=True)
async def cleanup():
    await _cleanup()
    yield
    await _cleanup()


# ── Registration sends verification email ─────────────────────────────


async def test_register_triggers_verification_email(
    client: AsyncClient,
) -> None:
    resp = await client.post(f"{API}/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body


# ── Verify Email ─────────────────────────────────────────────────────


async def test_verify_email_with_valid_token(client: AsyncClient) -> None:
    token = await _register(client)
    user_id = await _get_user_id(client, token)
    email = await _get_user_email(client, token)

    verify_token = create_email_verification_token(user_id, email)
    resp = await client.post(
        f"{API}/auth/verify-email",
        json={"token": verify_token},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Email verified successfully"

    me_resp = await client.get(
        f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.json()["is_verified"] is True


async def test_verify_email_rejects_invalid_token(client: AsyncClient) -> None:
    resp = await client.post(
        f"{API}/auth/verify-email",
        json={"token": "garbage-token"},
    )
    assert resp.status_code == 400


async def test_verify_email_already_verified(client: AsyncClient) -> None:
    token = await _register(client)
    user_id = await _get_user_id(client, token)
    email = await _get_user_email(client, token)

    vt = create_email_verification_token(user_id, email)
    await client.post(f"{API}/auth/verify-email", json={"token": vt})

    resp = await client.post(
        f"{API}/auth/verify-email", json={"token": vt}
    )
    assert resp.status_code == 200
    assert "already verified" in resp.json()["message"].lower()


async def test_verify_email_rejects_wrong_type_token(
    client: AsyncClient,
) -> None:
    token = await _register(client)
    user_id = await _get_user_id(client, token)

    access_token = create_access_token(user_id)
    resp = await client.post(
        f"{API}/auth/verify-email", json={"token": access_token}
    )
    assert resp.status_code == 400


# ── Resend Verification ──────────────────────────────────────────────


async def test_resend_verification_sends_email(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.post(
        f"{API}/auth/resend-verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "sent" in resp.json()["message"].lower()


async def test_resend_verification_skips_already_verified(
    client: AsyncClient,
) -> None:
    token = await _register(client)
    user_id = await _get_user_id(client, token)
    email = await _get_user_email(client, token)

    vt = create_email_verification_token(user_id, email)
    await client.post(f"{API}/auth/verify-email", json={"token": vt})

    resp = await client.post(
        f"{API}/auth/resend-verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "already verified" in resp.json()["message"].lower()


async def test_resend_verification_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(f"{API}/auth/resend-verification")
    assert resp.status_code in (401, 403)
