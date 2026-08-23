from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.core.exceptions import UnauthorizedException

import pytest


def test_password_hash_roundtrip() -> None:
    hashed = get_password_hash("s3cret-password")
    assert hashed != "s3cret-password"
    assert verify_password("s3cret-password", hashed)


def test_password_hash_rejects_wrong_password() -> None:
    hashed = get_password_hash("s3cret-password")
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip() -> None:
    token = create_access_token(subject="user-123")
    payload = verify_token(token, expected_type=ACCESS_TOKEN_TYPE)
    assert payload["sub"] == "user-123"


def test_refresh_token_roundtrip() -> None:
    token = create_refresh_token(subject="user-123")
    payload = verify_token(token, expected_type=REFRESH_TOKEN_TYPE)
    assert payload["sub"] == "user-123"


def test_verify_token_rejects_wrong_type() -> None:
    token = create_access_token(subject="user-123")
    with pytest.raises(UnauthorizedException):
        verify_token(token, expected_type=REFRESH_TOKEN_TYPE)


def test_verify_token_rejects_garbage() -> None:
    with pytest.raises(UnauthorizedException):
        verify_token("not-a-jwt")