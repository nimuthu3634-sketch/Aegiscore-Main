from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_and_verify_password_round_trip() -> None:
    password = "AegisCore123!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_create_access_token_and_decode_access_token() -> None:
    token = create_access_token("user-123")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert "exp" in payload

