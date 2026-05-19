"""API endpoint tests for ticket status lookup."""

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
def mock_ticket():
    """Mock ticket object."""
    ticket = MagicMock()
    ticket.id = uuid4()
    ticket.status = "open"
    ticket.category = "technical"
    ticket.priority = "medium"
    ticket.created_at = datetime.utcnow()
    ticket.resolved_at = None
    ticket.resolution_notes = None
    ticket.conversation_id = uuid4()
    return ticket


class TestTicketStatusEndpoint:
    """Tests for GET /support/ticket/{ticket_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_ticket_status_with_full_uuid(self, client, mock_ticket):
        """Test getting ticket status with full UUID."""
        with patch('backend.api.routes.tickets.ticket_repo') as mock_repo, \
             patch('backend.api.routes.tickets.db') as mock_db:

            mock_repo.get_by_id = AsyncMock(return_value=mock_ticket)

            # Mock database connection for messages
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            ticket_id = str(mock_ticket.id)
            response = client.get(f"/support/ticket/{ticket_id}")

            assert response.status_code == 200
            data = response.json()
            assert "ticket_id" in data
            assert data["status"] == "open"
            assert data["category"] == "technical"
            assert data["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_get_ticket_status_with_short_id(self, client, mock_ticket):
        """Test getting ticket status with short TICKET-XXXXXXXX format."""
        with patch('backend.api.routes.tickets.ticket_repo') as mock_repo, \
             patch('backend.api.routes.tickets.db') as mock_db:

            # Mock get_all to return list of tickets for prefix search
            mock_repo.get_all = AsyncMock(return_value=[mock_ticket])
            mock_repo.get_by_id = AsyncMock(return_value=mock_ticket)

            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Use first 8 chars of UUID
            short_id = f"TICKET-{str(mock_ticket.id)[:8].upper()}"
            response = client.get(f"/support/ticket/{short_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["ticket_id"].startswith("TICKET-")

    @pytest.mark.asyncio
    async def test_get_ticket_status_not_found(self, client):
        """Test getting status for non-existent ticket."""
        with patch('backend.api.routes.tickets.ticket_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(return_value=None)

            fake_uuid = str(uuid4())
            response = client.get(f"/support/ticket/{fake_uuid}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_ticket_status_invalid_id_format(self, client):
        """Test getting status with invalid ticket ID format."""
        response = client.get("/support/ticket/invalid-id-format")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_ticket_status_with_messages(self, client, mock_ticket):
        """Test getting ticket status includes conversation messages."""
        with patch('backend.api.routes.tickets.ticket_repo') as mock_repo, \
             patch('backend.api.routes.tickets.db') as mock_db:

            mock_repo.get_by_id = AsyncMock(return_value=mock_ticket)

            # Mock messages
            mock_messages = [
                {
                    "id": uuid4(),
                    "conversation_id": mock_ticket.conversation_id,
                    "channel": "web_form",
                    "direction": "inbound",
                    "role": "customer",
                    "content": "I need help",
                    "created_at": datetime.utcnow(),
                    "tokens_used": None,
                    "latency_ms": None,
                    "delivery_status": "delivered"
                },
                {
                    "id": uuid4(),
                    "conversation_id": mock_ticket.conversation_id,
                    "channel": "web_form",
                    "direction": "outbound",
                    "role": "agent",
                    "content": "How can I help you?",
                    "created_at": datetime.utcnow(),
                    "tokens_used": 50,
                    "latency_ms": 1200,
                    "delivery_status": "delivered"
                }
            ]

            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=mock_messages)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            ticket_id = str(mock_ticket.id)
            response = client.get(f"/support/ticket/{ticket_id}")

            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert len(data["messages"]) == 2
            assert data["messages"][0]["role"] == "customer"
            assert data["messages"][1]["role"] == "agent"

    @pytest.mark.asyncio
    async def test_get_ticket_status_resolved_ticket(self, client, mock_ticket):
        """Test getting status for resolved ticket."""
        with patch('backend.api.routes.tickets.ticket_repo') as mock_repo, \
             patch('backend.api.routes.tickets.db') as mock_db:

            # Set ticket as resolved
            mock_ticket.status = "resolved"
            mock_ticket.resolved_at = datetime.utcnow()
            mock_ticket.resolution_notes = "Issue resolved successfully"

            mock_repo.get_by_id = AsyncMock(return_value=mock_ticket)

            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            ticket_id = str(mock_ticket.id)
            response = client.get(f"/support/ticket/{ticket_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "resolved"
            assert data["resolved_at"] is not None
            assert data["resolution_notes"] == "Issue resolved successfully"

    @pytest.mark.asyncio
    async def test_get_ticket_status_database_error(self, client):
        """Test handling of database errors."""
        with patch('backend.api.routes.tickets.ticket_repo') as mock_repo:
            mock_repo.get_by_id = AsyncMock(side_effect=Exception("Database error"))

            ticket_id = str(uuid4())
            response = client.get(f"/support/ticket/{ticket_id}")

            assert response.status_code == 500
            assert "error" in response.json() or "detail" in response.json()
