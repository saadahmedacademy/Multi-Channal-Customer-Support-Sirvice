"""API endpoint tests for customer and authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from backend.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Valid API key for testing."""
    return "test-api-key-12345678901234567890123456789012"


@pytest.fixture
def mock_customer():
    """Mock customer object."""
    customer = MagicMock()
    customer.id = uuid4()
    customer.email = "test@example.com"
    customer.phone = "+1234567890"
    customer.name = "Test User"
    return customer


class TestCustomerLookupEndpoint:
    """Tests for GET /customers/lookup endpoint (requires auth)."""

    def test_customer_lookup_without_api_key(self, client):
        """Test customer lookup without API key returns 401."""
        response = client.get("/customers/lookup?email=test@example.com")
        assert response.status_code == 403  # Forbidden without API key

    @pytest.mark.asyncio
    async def test_customer_lookup_with_invalid_api_key(self, client):
        """Test customer lookup with invalid API key returns 403."""
        response = client.get(
            "/customers/lookup?email=test@example.com",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_customer_lookup_by_email(self, client, valid_api_key, mock_customer):
        """Test successful customer lookup by email."""
        with patch('backend.api.routes.customers.customer_repo') as mock_repo, \
             patch('backend.utils.auth.settings') as mock_settings:

            # Mock API key validation
            mock_settings.internal_api_keys = valid_api_key

            mock_repo.find_by_email = AsyncMock(return_value=mock_customer)

            response = client.get(
                "/customers/lookup?email=test@example.com",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 200
            data = response.json()
            assert "customer_id" in data
            assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_customer_lookup_by_phone(self, client, valid_api_key, mock_customer):
        """Test successful customer lookup by phone."""
        with patch('backend.api.routes.customers.customer_repo') as mock_repo, \
             patch('backend.utils.auth.settings') as mock_settings:

            mock_settings.internal_api_keys = valid_api_key
            mock_repo.find_by_phone = AsyncMock(return_value=mock_customer)

            response = client.get(
                "/customers/lookup?phone=%2B1234567890",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 200
            data = response.json()
            assert "customer_id" in data

    @pytest.mark.asyncio
    async def test_customer_lookup_not_found(self, client, valid_api_key):
        """Test customer lookup when customer doesn't exist."""
        with patch('backend.api.routes.customers.customer_repo') as mock_repo, \
             patch('backend.utils.auth.settings') as mock_settings:

            mock_settings.internal_api_keys = valid_api_key
            mock_repo.find_by_email = AsyncMock(return_value=None)

            response = client.get(
                "/customers/lookup?email=notfound@example.com",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 404

    def test_customer_lookup_missing_parameters(self, client, valid_api_key):
        """Test customer lookup without email or phone."""
        with patch('backend.utils.auth.settings') as mock_settings:
            mock_settings.internal_api_keys = valid_api_key

            response = client.get(
                "/customers/lookup",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 400


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test health check returns healthy status."""
        with patch('backend.api.main.db') as mock_db, \
             patch('backend.api.main.queue_client') as mock_queue, \
             patch('backend.api.main.settings') as mock_settings:

            # Mock database check
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Mock queue
            mock_queue.producer = MagicMock()

            # Mock settings
            mock_settings.openrouter_api_key = "test-key"
            mock_settings.meta_whatsapp_token = "test-token"
            mock_settings.meta_whatsapp_phone_id = "test-phone-id"
            mock_settings.gmail_oauth_token = "test-oauth"

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "channels" in data
            assert "services" in data

    @pytest.mark.asyncio
    async def test_health_check_database_error(self, client):
        """Test health check with database error."""
        with patch('backend.api.main.db') as mock_db, \
             patch('backend.api.main.queue_client') as mock_queue, \
             patch('backend.api.main.settings') as mock_settings:

            # Mock database error
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=Exception("DB connection failed"))
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            mock_queue.producer = MagicMock()
            mock_settings.openrouter_api_key = "test-key"

            response = client.get("/health")

            assert response.status_code == 200  # Still returns 200 but with degraded status
            data = response.json()
            assert data["status"] == "degraded"


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "AI Customer Support Agent API"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    def test_rate_limit_enforcement(self, client):
        """Test that rate limiting is enforced after threshold."""
        # Make requests up to the limit (10 per minute)
        for i in range(10):
            response = client.get("/")
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]

    def test_rate_limit_headers(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_health_endpoint_bypasses_rate_limit(self, client):
        """Test that health endpoint is not rate limited."""
        with patch('backend.api.main.db') as mock_db, \
             patch('backend.api.main.queue_client') as mock_queue, \
             patch('backend.api.main.settings') as mock_settings:

            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn
            mock_queue.producer = MagicMock()
            mock_settings.openrouter_api_key = "test-key"

            # Make many requests to health endpoint
            for i in range(20):
                response = client.get("/health")
                assert response.status_code == 200  # Should never be rate limited
