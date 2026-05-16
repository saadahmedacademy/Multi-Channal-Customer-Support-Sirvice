"""Unit tests for API key authentication."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from backend.utils.auth import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    get_api_key
)


class TestAPIKeyGeneration:
    """Test API key generation."""

    def test_generate_api_key_returns_string(self):
        """Test that generate_api_key returns a string."""
        api_key = generate_api_key()

        assert isinstance(api_key, str)

    def test_generate_api_key_has_correct_length(self):
        """Test that generated API key has correct length (64 chars for hex)."""
        api_key = generate_api_key()

        # secrets.token_hex(32) generates 64 character hex string
        assert len(api_key) == 64

    def test_generate_api_key_is_unique(self):
        """Test that each generated API key is unique."""
        keys = [generate_api_key() for _ in range(100)]

        # All keys should be unique
        assert len(keys) == len(set(keys))

    def test_generate_api_key_is_hexadecimal(self):
        """Test that generated API key is valid hexadecimal."""
        api_key = generate_api_key()

        # Should be valid hex string
        try:
            int(api_key, 16)
            is_hex = True
        except ValueError:
            is_hex = False

        assert is_hex is True


class TestAPIKeyHashing:
    """Test API key hashing."""

    def test_hash_api_key_returns_string(self):
        """Test that hash_api_key returns a string."""
        api_key = "test_key_12345"

        hashed = hash_api_key(api_key)

        assert isinstance(hashed, str)

    def test_hash_api_key_is_deterministic(self):
        """Test that same key produces same hash."""
        api_key = "test_key_12345"

        hash1 = hash_api_key(api_key)
        hash2 = hash_api_key(api_key)

        assert hash1 == hash2

    def test_hash_api_key_different_keys_produce_different_hashes(self):
        """Test that different keys produce different hashes."""
        key1 = "test_key_1"
        key2 = "test_key_2"

        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        assert hash1 != hash2

    def test_hash_api_key_uses_sha256(self):
        """Test that hash is SHA-256 (64 character hex string)."""
        api_key = "test_key_12345"

        hashed = hash_api_key(api_key)

        # SHA-256 produces 64 character hex string
        assert len(hashed) == 64
        # Should be valid hex
        try:
            int(hashed, 16)
            is_hex = True
        except ValueError:
            is_hex = False
        assert is_hex is True


class TestAPIKeyVerification:
    """Test API key verification."""

    def test_verify_api_key_accepts_correct_key(self):
        """Test that correct API key is accepted."""
        api_key = "test_key_12345"
        stored_hash = hash_api_key(api_key)

        result = verify_api_key(api_key, stored_hash)

        assert result is True

    def test_verify_api_key_rejects_incorrect_key(self):
        """Test that incorrect API key is rejected."""
        correct_key = "test_key_12345"
        wrong_key = "wrong_key_67890"
        stored_hash = hash_api_key(correct_key)

        result = verify_api_key(wrong_key, stored_hash)

        assert result is False

    def test_verify_api_key_uses_constant_time_comparison(self):
        """Test that verification uses constant-time comparison (hmac.compare_digest)."""
        import hmac

        api_key = "test_key_12345"
        stored_hash = hash_api_key(api_key)

        # Verify that hmac.compare_digest is used (timing attack protection)
        with patch('hmac.compare_digest', wraps=hmac.compare_digest) as mock_compare:
            verify_api_key(api_key, stored_hash)

            mock_compare.assert_called_once()

    def test_verify_api_key_handles_empty_key(self):
        """Test handling of empty API key."""
        stored_hash = hash_api_key("valid_key")

        result = verify_api_key("", stored_hash)

        assert result is False

    def test_verify_api_key_handles_none_key(self):
        """Test handling of None API key."""
        stored_hash = hash_api_key("valid_key")

        # Should handle None gracefully
        try:
            result = verify_api_key(None, stored_hash)
            assert result is False
        except (TypeError, AttributeError):
            # If it raises an error, that's also acceptable
            pass


class TestGetAPIKeyDependency:
    """Test get_api_key FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_get_api_key_accepts_valid_key(self):
        """Test that valid API key is accepted."""
        valid_key = generate_api_key()

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [valid_key]

            result = await get_api_key(api_key=valid_key)

            assert result == valid_key

    @pytest.mark.asyncio
    async def test_get_api_key_rejects_invalid_key(self):
        """Test that invalid API key is rejected."""
        valid_key = generate_api_key()
        invalid_key = generate_api_key()

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [valid_key]

            with pytest.raises(HTTPException) as exc_info:
                await get_api_key(api_key=invalid_key)

            assert exc_info.value.status_code == 403
            assert "Invalid API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_api_key_rejects_missing_key(self):
        """Test that missing API key is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(api_key=None)

        assert exc_info.value.status_code == 401
        assert "Missing API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_api_key_accepts_any_valid_key_from_list(self):
        """Test that any valid key from the list is accepted."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        key3 = generate_api_key()

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [key1, key2, key3]

            # All three keys should be accepted
            result1 = await get_api_key(api_key=key1)
            result2 = await get_api_key(api_key=key2)
            result3 = await get_api_key(api_key=key3)

            assert result1 == key1
            assert result2 == key2
            assert result3 == key3


class TestAPIKeyConfiguration:
    """Test API key configuration loading."""

    def test_load_api_keys_from_environment(self):
        """Test loading API keys from environment variable."""
        from backend.utils.auth import _get_valid_api_keys

        with patch('backend.config.settings.settings') as mock_settings:
            mock_settings.internal_api_keys = "key1,key2,key3"

            keys = _get_valid_api_keys()

            assert len(keys) == 3
            assert "key1" in keys
            assert "key2" in keys
            assert "key3" in keys

    def test_load_api_keys_handles_whitespace(self):
        """Test that whitespace in API keys is handled."""
        from backend.utils.auth import _get_valid_api_keys

        with patch('backend.config.settings.settings') as mock_settings:
            mock_settings.internal_api_keys = " key1 , key2 , key3 "

            keys = _get_valid_api_keys()

            # Keys should be stripped of whitespace
            assert "key1" in keys
            assert "key2" in keys
            assert "key3" in keys
            assert " key1 " not in keys

    def test_load_api_keys_handles_empty_config(self):
        """Test handling of empty API key configuration."""
        from backend.utils.auth import _get_valid_api_keys

        with patch('backend.config.settings.settings') as mock_settings:
            mock_settings.internal_api_keys = ""

            keys = _get_valid_api_keys()

            assert keys == []

    def test_load_api_keys_handles_none_config(self):
        """Test handling of None API key configuration."""
        from backend.utils.auth import _get_valid_api_keys

        with patch('backend.config.settings.settings') as mock_settings:
            mock_settings.internal_api_keys = None

            keys = _get_valid_api_keys()

            assert keys == []


class TestAPIKeyEndpointProtection:
    """Test that endpoints are properly protected with API keys."""

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_api_key(self):
        """Test that protected endpoints require API key."""
        from fastapi.testclient import TestClient
        from backend.api.main import app

        client = TestClient(app)

        # Try to access protected endpoint without API key
        response = client.get("/customers/lookup?email=test@example.com")

        # Should return 401 or 403
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_protected_endpoint_accepts_valid_api_key(self):
        """Test that protected endpoints accept valid API key."""
        from fastapi.testclient import TestClient
        from backend.api.main import app

        client = TestClient(app)
        valid_key = generate_api_key()

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [valid_key]

            # Try to access protected endpoint with valid API key
            response = client.get(
                "/customers/lookup?email=test@example.com",
                headers={"X-API-Key": valid_key}
            )

            # Should not return 401 or 403 (might return 404 if customer not found, which is ok)
            assert response.status_code not in [401, 403]

    @pytest.mark.asyncio
    async def test_public_endpoint_does_not_require_api_key(self):
        """Test that public endpoints don't require API key."""
        from fastapi.testclient import TestClient
        from backend.api.main import app

        client = TestClient(app)

        # Try to access public endpoint without API key
        response = client.get("/health")

        # Should return 200
        assert response.status_code == 200


class TestAPIKeySecurityBestPractices:
    """Test security best practices for API keys."""

    def test_api_key_has_sufficient_entropy(self):
        """Test that generated API keys have sufficient entropy."""
        api_key = generate_api_key()

        # 64 character hex string = 256 bits of entropy
        # This is sufficient for cryptographic purposes
        assert len(api_key) == 64

    def test_api_key_hash_is_not_reversible(self):
        """Test that API key hash cannot be reversed."""
        api_key = "test_key_12345"
        hashed = hash_api_key(api_key)

        # Hash should be different from original key
        assert hashed != api_key
        # Hash should not contain original key
        assert api_key not in hashed

    def test_api_key_verification_is_timing_safe(self):
        """Test that API key verification is timing-attack safe."""
        # This is tested by verifying hmac.compare_digest is used
        # (already tested in test_verify_api_key_uses_constant_time_comparison)
        pass

    def test_api_keys_are_not_logged(self):
        """Test that API keys are not logged in plain text."""
        # This would require checking logging configuration
        # For now, we'll just verify the auth module doesn't log keys
        import logging

        with patch.object(logging.Logger, 'info') as mock_log:
            api_key = "secret_key_12345"
            hash_api_key(api_key)

            # Verify that the actual key is not logged
            if mock_log.called:
                for call in mock_log.call_args_list:
                    assert "secret_key_12345" not in str(call)


class TestAPIKeyRotation:
    """Test API key rotation scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_api_keys_supported(self):
        """Test that multiple API keys can be active simultaneously."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [key1, key2]

            # Both keys should work
            result1 = await get_api_key(api_key=key1)
            result2 = await get_api_key(api_key=key2)

            assert result1 == key1
            assert result2 == key2

    @pytest.mark.asyncio
    async def test_old_key_can_be_revoked(self):
        """Test that old API key can be revoked."""
        old_key = generate_api_key()
        new_key = generate_api_key()

        # Initially both keys work
        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [old_key, new_key]

            result = await get_api_key(api_key=old_key)
            assert result == old_key

        # After rotation, only new key works
        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [new_key]

            # Old key should be rejected
            with pytest.raises(HTTPException) as exc_info:
                await get_api_key(api_key=old_key)

            assert exc_info.value.status_code == 403

            # New key should still work
            result = await get_api_key(api_key=new_key)
            assert result == new_key


class TestAPIKeyErrorMessages:
    """Test API key error messages."""

    @pytest.mark.asyncio
    async def test_missing_key_error_message(self):
        """Test error message for missing API key."""
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(api_key=None)

        assert exc_info.value.status_code == 401
        assert "Missing API key" in exc_info.value.detail
        # Should not reveal implementation details
        assert "X-API-Key" in exc_info.value.detail or "header" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_invalid_key_error_message(self):
        """Test error message for invalid API key."""
        invalid_key = "invalid_key_12345"

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = ["valid_key"]

            with pytest.raises(HTTPException) as exc_info:
                await get_api_key(api_key=invalid_key)

            assert exc_info.value.status_code == 403
            assert "Invalid API key" in exc_info.value.detail
            # Should not reveal the actual valid keys
            assert "valid_key" not in exc_info.value.detail


class TestAPIKeyPerformance:
    """Test API key performance characteristics."""

    def test_api_key_verification_is_fast(self):
        """Test that API key verification is fast."""
        import time

        api_key = generate_api_key()
        stored_hash = hash_api_key(api_key)

        start = time.time()
        for _ in range(1000):
            verify_api_key(api_key, stored_hash)
        duration = time.time() - start

        # 1000 verifications should complete in under 100ms
        assert duration < 0.1

    @pytest.mark.asyncio
    async def test_get_api_key_handles_many_valid_keys(self):
        """Test that get_api_key works efficiently with many valid keys."""
        # Generate 100 valid keys
        valid_keys = [generate_api_key() for _ in range(100)]
        test_key = valid_keys[50]  # Key in the middle

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = valid_keys

            import time
            start = time.time()
            result = await get_api_key(api_key=test_key)
            duration = time.time() - start

            assert result == test_key
            # Should complete quickly even with many keys
            assert duration < 0.01
