"""API endpoint tests for metrics, conversations, and webhooks."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from backend.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_api_key():
    """Valid API key for testing."""
    return "test-api-key-12345678901234567890123456789012"


class TestMetricsEndpoint:
    """Tests for GET /metrics/channels endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_requires_authentication(self, client):
        """Test that metrics endpoint requires API key."""
        response = client.get("/metrics/channels")
        assert response.status_code in [401, 403]  # Either unauthorized or forbidden

    @pytest.mark.asyncio
    async def test_get_channel_metrics_success(self, client, valid_api_key):
        """Test successful retrieval of channel metrics."""
        with patch('backend.api.routes.metrics.db') as mock_db, \
             patch('backend.utils.auth.settings') as mock_settings, \
             patch('backend.api.routes.metrics.whatsapp_client') as mock_whatsapp, \
             patch('backend.api.routes.metrics.gmail_client') as mock_gmail:

            mock_settings.internal_api_keys = valid_api_key

            # Mock database queries
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(side_effect=[
                # Ticket counts
                [{"source_channel": "web_form", "status": "open", "count": 10}],
                # Message counts
                [{"channel": "web_form", "direction": "inbound", "count": 20}],
                # Response times
                [{"channel": "web_form", "avg_response_seconds": 120.5}],
                # Today's stats
                [{"source_channel": "web_form", "count": 5}]
            ])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Mock rate limit status
            mock_whatsapp.get_rate_limit_status = MagicMock(return_value={"remaining": 900, "limit": 1000})
            mock_gmail.get_rate_limit_status = MagicMock(return_value={"remaining": 450, "limit": 500})

            response = client.get(
                "/metrics/channels",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 200
            data = response.json()
            assert "tickets" in data
            assert "messages" in data
            assert "response_times" in data
            assert "channels" in data
            assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_get_ticket_summary_success(self, client):
        """Test successful retrieval of ticket summary."""
        with patch('backend.api.routes.metrics.db') as mock_db:

            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[
                {
                    "date": datetime.utcnow().date(),
                    "source_channel": "web_form",
                    "status": "open",
                    "count": 5
                }
            ])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            response = client.get("/metrics/tickets/summary?days=7")

            assert response.status_code == 200
            data = response.json()
            assert "period_days" in data
            assert data["period_days"] == 7
            assert "by_date" in data

    @pytest.mark.asyncio
    async def test_get_ticket_summary_custom_days(self, client):
        """Test ticket summary with custom day range."""
        with patch('backend.api.routes.metrics.db') as mock_db:

            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            response = client.get("/metrics/tickets/summary?days=30")

            assert response.status_code == 200
            data = response.json()
            assert data["period_days"] == 30


class TestConversationsEndpoint:
    """Tests for /conversations endpoints."""

    @pytest.mark.asyncio
    async def test_get_conversation_requires_auth(self, client):
        """Test that conversation endpoint requires API key."""
        conversation_id = str(uuid4())
        response = client.get(f"/conversations/{conversation_id}")
        assert response.status_code in [401, 403]  # Either unauthorized or forbidden

    @pytest.mark.asyncio
    async def test_get_conversation_success(self, client, valid_api_key):
        """Test successful conversation retrieval."""
        with patch('backend.api.routes.conversations.conversation_repo') as mock_repo, \
             patch('backend.api.routes.conversations.db') as mock_db, \
             patch('backend.utils.auth.settings') as mock_settings:

            mock_settings.internal_api_keys = valid_api_key

            # Mock conversation
            mock_conversation = MagicMock()
            mock_conversation.id = uuid4()
            mock_conversation.to_dict = MagicMock(return_value={
                "id": str(mock_conversation.id),
                "status": "active"
            })
            mock_repo.get_by_id = AsyncMock(return_value=mock_conversation)

            # Mock messages
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[
                {
                    "id": uuid4(),
                    "conversation_id": mock_conversation.id,
                    "channel": "web_form",
                    "direction": "inbound",
                    "role": "customer",
                    "content": "Hello",
                    "created_at": datetime.utcnow(),
                    "tokens_used": None,
                    "latency_ms": None,
                    "delivery_status": "delivered"
                }
            ])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            response = client.get(
                f"/conversations/{mock_conversation.id}",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 200
            data = response.json()
            assert "conversation" in data
            assert "messages" in data
            assert "message_count" in data
            assert data["message_count"] == 1

    @pytest.mark.asyncio
    async def test_get_conversation_invalid_uuid(self, client, valid_api_key):
        """Test conversation retrieval with invalid UUID."""
        with patch('backend.utils.auth.settings') as mock_settings:
            mock_settings.internal_api_keys = valid_api_key

            response = client.get(
                "/conversations/invalid-uuid",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 400
            assert "Invalid conversation ID" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, client, valid_api_key):
        """Test conversation retrieval when conversation doesn't exist."""
        with patch('backend.api.routes.conversations.conversation_repo') as mock_repo, \
             patch('backend.utils.auth.settings') as mock_settings:

            mock_settings.internal_api_keys = valid_api_key
            mock_repo.get_by_id = AsyncMock(return_value=None)

            conversation_id = str(uuid4())
            response = client.get(
                f"/conversations/{conversation_id}",
                headers={"X-API-Key": valid_api_key}
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, client):
        """Test successful conversation history retrieval."""
        with patch('backend.api.routes.conversations.db') as mock_db:

            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[
                {
                    "id": uuid4(),
                    "conversation_id": uuid4(),
                    "channel": "web_form",
                    "direction": "inbound",
                    "role": "customer",
                    "content": "Message 1",
                    "created_at": datetime.utcnow(),
                    "tokens_used": None,
                    "latency_ms": None,
                    "delivery_status": "delivered"
                }
            ])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            conversation_id = str(uuid4())
            response = client.get(f"/conversations/{conversation_id}/history?limit=10")

            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert "count" in data
            assert data["conversation_id"] == conversation_id


class TestWhatsAppWebhook:
    """Tests for WhatsApp webhook endpoints."""

    def test_whatsapp_webhook_verify_success(self, client):
        """Test successful WhatsApp webhook verification."""
        with patch('backend.api.routes.whatsapp.settings') as mock_settings:
            mock_settings.whatsapp_verify_token = "test_verify_token"

            response = client.get(
                "/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=test_verify_token&hub.challenge=test_challenge"
            )

            assert response.status_code == 200
            assert response.text == "test_challenge"

    def test_whatsapp_webhook_verify_invalid_token(self, client):
        """Test WhatsApp webhook verification with invalid token."""
        with patch('backend.api.routes.whatsapp.settings') as mock_settings:
            mock_settings.whatsapp_verify_token = "correct_token"

            response = client.get(
                "/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=test_challenge"
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_receive_message(self, client):
        """Test receiving WhatsApp message via webhook."""
        with patch('backend.api.routes.whatsapp.settings') as mock_settings, \
             patch('backend.api.routes.whatsapp.queue_client') as mock_queue:

            mock_settings.is_production = False  # Skip signature verification
            mock_queue.publish = AsyncMock()

            webhook_payload = {
                "entry": [{
                    "id": "business_account_id",
                    "changes": [{
                        "field": "messages",
                        "value": {
                            "messages": [{
                                "from": "+1234567890",
                                "id": "wamid.123456",
                                "timestamp": "1234567890",
                                "type": "text",
                                "text": {"body": "Hello"}
                            }]
                        }
                    }]
                }]
            }

            response = client.post("/webhooks/whatsapp", json=webhook_payload)

            assert response.status_code == 200
            assert response.text == "EVENT_RECEIVED"
            mock_queue.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_invalid_json(self, client):
        """Test WhatsApp webhook with invalid JSON."""
        with patch('backend.api.routes.whatsapp.settings') as mock_settings:
            mock_settings.is_production = False

            response = client.post(
                "/webhooks/whatsapp",
                data="invalid json",
                headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_status_update(self, client):
        """Test WhatsApp message status update."""
        with patch('backend.api.routes.whatsapp.settings') as mock_settings, \
             patch('backend.api.routes.whatsapp.db') as mock_db:

            mock_settings.is_production = False
            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            webhook_payload = {
                "entry": [{
                    "id": "business_account_id",
                    "changes": [{
                        "field": "messages",
                        "value": {
                            "statuses": [{
                                "id": "wamid.123456",
                                "status": "delivered",
                                "timestamp": "1234567890",
                                "recipient_id": "+1234567890"
                            }]
                        }
                    }]
                }]
            }

            response = client.post("/webhooks/whatsapp", json=webhook_payload)

            assert response.status_code == 200
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_whatsapp_webhook_signature_verification(self, client):
        """Test WhatsApp webhook signature verification in production."""
        with patch('backend.api.routes.whatsapp.settings') as mock_settings:
            mock_settings.is_production = True
            mock_settings.whatsapp_app_secret = "test_secret"

            # Invalid signature
            response = client.post(
                "/webhooks/whatsapp",
                json={"entry": []},
                headers={"X-Hub-Signature-256": "sha256=invalid"}
            )

            assert response.status_code == 401
