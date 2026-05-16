"""API tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.api.main import app
from backend.utils.auth import generate_api_key


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Generate valid API key for testing."""
    return generate_api_key()


class TestAPIKeyAuthentication:
    """Test API key authentication on protected endpoints."""

    def test_protected_endpoint_without_api_key(self, client):
        """Test that protected endpoint rejects request without API key."""
        response = client.get("/customers/lookup?email=test@example.com")

        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data

    def test_protected_endpoint_with_invalid_api_key(self, client):
        """Test that protected endpoint rejects invalid API key."""
        response = client.get(
            "/customers/lookup?email=test@example.com",
            headers={"X-API-Key": "invalid_key_12345"}
        )

        assert response.status_code == 403
        data = response.json()
        assert "Invalid API key" in data["detail"]

    def test_protected_endpoint_with_valid_api_key(self, client, valid_api_key):
        """Test that protected endpoint accepts valid API key."""
        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [valid_api_key]

            response = client.get(
                "/customers/lookup?email=test@example.com",
                headers={"X-API-Key": valid_api_key}
            )

            # Should not return 401 or 403
            assert response.status_code not in [401, 403]

    def test_public_endpoint_without_api_key(self, client):
        """Test that public endpoints don't require API key."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_api_key_in_wrong_header(self, client, valid_api_key):
        """Test that API key in wrong header is rejected."""
        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [valid_api_key]

            response = client.get(
                "/customers/lookup?email=test@example.com",
                headers={"Authorization": f"Bearer {valid_api_key}"}  # Wrong header
            )

            assert response.status_code in [401, 403]

    def test_multiple_valid_api_keys(self, client):
        """Test that any valid API key from list is accepted."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        with patch('backend.utils.auth._get_valid_api_keys') as mock_get_keys:
            mock_get_keys.return_value = [key1, key2]

            # Both keys should work
            response1 = client.get(
                "/customers/lookup?email=test@example.com",
                headers={"X-API-Key": key1}
            )
            response2 = client.get(
                "/customers/lookup?email=test@example.com",
                headers={"X-API-Key": key2}
            )

            assert response1.status_code not in [401, 403]
            assert response2.status_code not in [401, 403]


class TestProtectedEndpoints:
    """Test that all protected endpoints require authentication."""

    def test_customers_lookup_requires_auth(self, client):
        """Test /customers/lookup requires API key."""
        response = client.get("/customers/lookup?email=test@example.com")
        assert response.status_code in [401, 403]

    def test_conversations_endpoint_requires_auth(self, client):
        """Test /conversations/{id} requires API key."""
        from uuid import uuid4
        conversation_id = str(uuid4())

        response = client.get(f"/conversations/{conversation_id}")
        assert response.status_code in [401, 403, 404]

    def test_metrics_endpoint_requires_auth(self, client):
        """Test /metrics/channels requires API key."""
        response = client.get("/metrics/channels")
        assert response.status_code in [401, 403]


class TestAPIKeyErrorMessages:
    """Test API key error messages."""

    def test_missing_api_key_error_message(self, client):
        """Test error message when API key is missing."""
        response = client.get("/customers/lookup?email=test@example.com")

        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data
        # Should mention API key or authentication
        assert any(word in data["detail"].lower() for word in ["api", "key", "auth"])

    def test_invalid_api_key_error_message(self, client):
        """Test error message when API key is invalid."""
        response = client.get(
            "/customers/lookup?email=test@example.com",
            headers={"X-API-Key": "invalid_key"}
        )

        assert response.status_code == 403
        data = response.json()
        assert "Invalid API key" in data["detail"]
