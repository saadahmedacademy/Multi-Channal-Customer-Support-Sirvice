"""
API endpoint tests.

Tests for all REST API endpoints using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Fixtures ==============

@pytest.fixture
def test_client():
    """Create test client for API testing."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Create proper async mocks
    mock_queue = AsyncMock()
    mock_queue.start_producer = AsyncMock()
    mock_queue.stop_producer = AsyncMock()
    mock_queue.producer = None
    
    # Disable rate limiting for tests
    with patch('backend.api.main.RateLimitMiddleware'):
        with patch('backend.db.connection.init_db', AsyncMock()):
            with patch('backend.db.connection.close_db', AsyncMock()):
                with patch('backend.integrations.queue_client.queue_client', mock_queue):
                    from backend.api.main import app
                    # Remove rate limit middleware for testing
                    app.user_middleware = [m for m in app.user_middleware if 'RateLimit' not in str(m)]
                    with TestClient(app, raise_server_exceptions=False) as client:
                        yield client


@pytest.fixture
def mock_ticket_repo():
    """Mock ticket repository."""
    with patch('backend.api.routes.tickets.ticket_repo') as mock:
        yield mock


@pytest.fixture
def mock_customer_repo():
    """Mock customer repository."""
    with patch('backend.api.routes.web_form.customer_repo') as mock:
        yield mock


@pytest.fixture
def mock_conversation_repo():
    """Mock conversation repository."""
    with patch('backend.api.routes.web_form.conversation_repo') as mock:
        yield mock


# ============== Health Check Tests ==============

class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_health_check(self, test_client):
        """Test health check endpoint returns healthy status."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "timestamp" in data
        assert "channels" in data
        assert "services" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_health_check_channels(self, test_client):
        """Test health check includes channel status."""
        response = test_client.get("/health")
        data = response.json()
        
        assert "web_form" in data["channels"]
        assert "whatsapp" in data["channels"]
        assert "email" in data["channels"]

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_root_endpoint(self, test_client):
        """Test root endpoint."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


# ============== Web Form Tests ==============

class TestWebFormSubmission:
    """Tests for web form submission endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_submit_valid_form(self, test_client, mock_customer_repo,
                                mock_conversation_repo, mock_ticket_repo):
        """Test valid form submission."""
        # Setup mocks
        mock_customer = MagicMock()
        mock_customer.id = uuid4()
        mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
        
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation_repo.get_active_by_customer = AsyncMock(return_value=None)
        mock_conversation_repo.create = AsyncMock(return_value=mock_conversation)
        
        mock_ticket = MagicMock()
        mock_ticket.id = uuid4()
        mock_ticket.status = "open"
        mock_ticket_repo.get_by_conversation_id = AsyncMock(return_value=None)
        mock_ticket_repo.create = AsyncMock(return_value=mock_ticket)
        
        with patch('backend.api.routes.web_form.db'):
            with patch('backend.api.routes.web_form.queue_client.publish', AsyncMock()):
                response = test_client.post("/support/submit", json={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "subject": "Test Issue",
                    "category": "technical",
                    "priority": "medium",
                    "message": "I need help with API authentication"
                })
        
        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert "message" in data
        assert "status" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_submit_missing_required_field(self, test_client):
        """Test form submission with missing required field."""
        response = test_client.post("/support/submit", json={
            "name": "John Doe",
            # Missing email
            "subject": "Test",
            "message": "Test message"
        })
        
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_submit_invalid_email(self, test_client):
        """Test form submission with invalid email."""
        response = test_client.post("/support/submit", json={
            "name": "John Doe",
            "email": "invalid-email",
            "subject": "Test",
            "category": "technical",
            "message": "Test message"
        })
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_submit_short_message(self, test_client):
        """Test form submission with very short message."""
        response = test_client.post("/support/submit", json={
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test",
            "category": "technical",
            "message": "Hi"  # Too short
        })
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_submit_with_phone(self, test_client, mock_customer_repo,
                               mock_conversation_repo, mock_ticket_repo):
        """Test form submission with phone number."""
        mock_customer = MagicMock()
        mock_customer.id = uuid4()
        mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
        
        mock_conversation = MagicMock()
        mock_conversation.id = uuid4()
        mock_conversation_repo.get_active_by_customer = AsyncMock(return_value=None)
        mock_conversation_repo.create = AsyncMock(return_value=mock_conversation)
        
        mock_ticket = MagicMock()
        mock_ticket.id = uuid4()
        mock_ticket.status = "open"
        mock_ticket_repo.create = AsyncMock(return_value=mock_ticket)
        
        with patch('backend.api.routes.web_form.db'):
            with patch('backend.api.routes.web_form.queue_client.publish', AsyncMock()):
                response = test_client.post("/support/submit", json={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+14155551234",
                    "subject": "Test",
                    "category": "technical",
                    "message": "Test message"
                })
        
        assert response.status_code == 200


# ============== Ticket Status Tests ==============

class TestTicketStatus:
    """Tests for ticket status lookup endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_get_ticket_status(self, test_client, mock_ticket_repo):
        """Test getting ticket status by ID."""
        mock_ticket = MagicMock()
        ticket_id = uuid4()
        mock_ticket.id = ticket_id
        mock_ticket.conversation_id = uuid4()
        mock_ticket.customer_id = uuid4()
        mock_ticket.status = "open"
        mock_ticket.priority = "medium"
        mock_ticket.created_at = MagicMock()
        mock_ticket.to_dict.return_value = {"id": str(ticket_id)}
        
        mock_ticket_repo.get_by_id = AsyncMock(return_value=mock_ticket)
        
        with patch('backend.api.routes.tickets.db') as mock_db:
            mock_db.acquire.return_value.__aenter__.return_value.fetch = AsyncMock(return_value=[])
            
            response = test_client.get(f"/support/ticket/{ticket_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "ticket_id" in data
        assert "status" in data
        assert "messages" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_get_ticket_not_found(self, test_client, mock_ticket_repo):
        """Test getting non-existent ticket."""
        mock_ticket_repo.get_by_id = AsyncMock(return_value=None)
        
        response = test_client.get("/support/ticket/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_get_ticket_invalid_uuid(self, test_client):
        """Test getting ticket with invalid UUID format."""
        response = test_client.get("/support/ticket/invalid-uuid")
        
        assert response.status_code in [400, 404]


# ============== WhatsApp Webhook Tests ==============

class TestWhatsAppWebhook:
    """Tests for WhatsApp webhook endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_whatsapp_webhook_verify(self, test_client):
        """Test WhatsApp webhook verification (GET)."""
        from backend.config.settings import settings
        response = test_client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": settings.whatsapp_verify_token,
                "hub.challenge": "test-challenge"
            }
        )

        assert response.status_code == 200
        assert response.text == "test-challenge"

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_whatsapp_webhook_verify_failed(self, test_client):
        """Test WhatsApp webhook verification failure."""
        response = test_client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "test-challenge"
            }
        )
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_whatsapp_receive_message(self, test_client, sample_whatsapp_message):
        """Test receiving WhatsApp message."""
        with patch('backend.api.routes.whatsapp._handle_incoming_message', AsyncMock()):
            response = test_client.post(
                "/webhooks/whatsapp",
                json=sample_whatsapp_message,
                headers={"X-Hub-Signature-256": "sha256=test"}
            )
        
        assert response.status_code == 200
        assert response.text == "EVENT_RECEIVED"

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_whatsapp_invalid_json(self, test_client):
        """Test WhatsApp webhook with invalid JSON."""
        response = test_client.post(
            "/webhooks/whatsapp",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400


# ============== Customer Lookup Tests ==============

class TestCustomerLookup:
    """Tests for customer lookup endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_lookup_customer_by_email(self, test_client):
        """Test looking up customer by email."""
        mock_customer = MagicMock()
        mock_customer.id = uuid4()
        mock_customer.to_dict.return_value = {"email": "test@example.com"}
        
        with patch('backend.api.routes.customers.customer_repo') as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=mock_customer)
            
            with patch('backend.api.routes.customers.customer_identifier_repo') as mock_id_repo:
                mock_id_repo.get_all_identifiers = AsyncMock(return_value=[])
                
                response = test_client.get("/customers/lookup?email=test@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert "customer" in data
        assert "identifiers" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_lookup_customer_not_found(self, test_client):
        """Test looking up non-existent customer."""
        with patch('backend.api.routes.customers.customer_repo') as mock_repo:
            mock_repo.get_by_email = AsyncMock(return_value=None)
            mock_repo.get_by_phone = AsyncMock(return_value=None)
            
            response = test_client.get("/customers/lookup?email=notfound@example.com")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_lookup_no_params(self, test_client):
        """Test lookup without email or phone."""
        response = test_client.get("/customers/lookup")
        
        assert response.status_code == 400


# ============== Metrics Tests ==============

class TestMetricsEndpoint:
    """Tests for metrics endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_get_channel_metrics(self, test_client):
        """Test getting channel metrics."""
        with patch('backend.api.routes.metrics.db') as mock_db:
            mock_db.acquire.return_value.__aenter__.return_value.fetch = AsyncMock(return_value=[])
            
            response = test_client.get("/metrics/channels")
        
        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "tickets" in data
        assert "messages" in data
        assert "response_times" in data

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_get_ticket_summary(self, test_client):
        """Test getting ticket summary."""
        with patch('backend.api.routes.metrics.db') as mock_db:
            mock_db.acquire.return_value.__aenter__.return_value.fetch = AsyncMock(return_value=[])
            
            response = test_client.get("/metrics/tickets/summary?days=7")
        
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "by_date" in data


# ============== Rate Limiting Tests ==============

class TestRateLimiting:
    """Tests for rate limiting middleware."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_rate_limit_headers(self, test_client):
        """Test that rate limit headers are present."""
        response = test_client.get("/health")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "api"])
