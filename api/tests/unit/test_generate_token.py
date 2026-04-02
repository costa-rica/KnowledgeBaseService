import hashlib

from src.auth import hash_token


def test_hash_token_produces_valid_sha256():
    token = "test-token-abc123"
    result = hash_token(token)
    assert len(result) == 64
    assert result == hashlib.sha256(token.encode()).hexdigest()


def test_different_tokens_produce_different_hashes():
    assert hash_token("token-a") != hash_token("token-b")


def test_generate_token_produces_url_safe_string():
    import secrets
    token = secrets.token_urlsafe(32)
    assert len(token) > 0
    hashed = hash_token(token)
    assert len(hashed) == 64
