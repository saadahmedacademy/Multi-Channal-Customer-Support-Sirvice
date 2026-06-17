"""API endpoint tests for web form submission."""

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
def mock_customer():
    """Mock customer object."""
    customer = MagicMock()
    customer.id = uuid4()
    customer.email = "test@example.com"
    customer.name = "Test User"
    return customer


@pytest.fixture
def mock_conversation():
    """Mock conversation object."""
    conversation = MagicMock()
    conversation.id = uuid4()
    return conversation


@pytest.fixture
def mock_ticket():
    """Mock ticket object."""
    ticket = MagicMock()
    ticket.id = uuid4()
    ticket.status = "open"
    return ticket


class TestWebFormSubmission:
    """Tests for POST /support/submit endpoint."""

    @pytest.mark.asyncio
    async def test_submit_valid_form(self, client, mock_customer, mock_conversation, mock_ticket):
        """Test successful form submission with valid data."""
        with patch('backend.api.routes.web_form.customer_repo') as mock_customer_repo, \
             patch('backend.api.routes.web_form.conversation_repo') as mock_conv_repo, \
             patch('backend.api.routes.web_form.ticket_repo') as mock_ticket_repo, \
             patch('backend.api.routes.web_form.queue_client') as mock_queue, \
             patch('backend.api.routes.web_form.db') as mock_db:

            # Setup mocks
            mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
            mock_conv_repo.create = AsyncMock(return_value=mock_conversation)
            mock_ticket_repo.create = AsyncMock(return_value=mock_ticket)
            mock_queue.publish = AsyncMock()

            # Mock database connection
            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Valid form data
            form_data = {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "subject": "Need help with product",
                "category": "technical",
                "priority": "medium",
                "message": "I'm having trouble with the login feature. Can you help?"
            }

            response = client.post("/support/submit", json=form_data)

            assert response.status_code == 200
            data = response.json()
            assert "ticket_id" in data
            assert data["ticket_id"].startswith("TICKET-")
            assert "message" in data
            assert "Thank you" in data["message"]
            assert data["status"] == "open"

    def test_submit_form_missing_required_fields(self, client):
        """Test form submission with missing required fields."""
        incomplete_data = {
            "name": "John Doe",
            "email": "john@example.com"
            # Missing subject, category, message
        }

        response = client.post("/support/submit", json=incomplete_data)
        assert response.status_code == 422  # Validation error

    def test_submit_form_invalid_email(self, client):
        """Test form submission with invalid email format."""
        invalid_data = {
            "name": "John Doe",
            "email": "not-an-email",
            "subject": "Test subject",
            "category": "general",
            "priority": "medium",
            "message": "This is a test message with enough characters."
        }

        response = client.post("/support/submit", json=invalid_data)
        assert response.status_code == 422

    def test_submit_form_xss_attempt(self, client, mock_customer, mock_conversation, mock_ticket):
        """Test that XSS attempts are sanitized."""
        with patch('backend.api.routes.web_form.customer_repo') as mock_customer_repo, \
             patch('backend.api.routes.web_form.conversation_repo') as mock_conv_repo, \
             patch('backend.api.routes.web_form.ticket_repo') as mock_ticket_repo, \
             patch('backend.api.routes.web_form.queue_client') as mock_queue, \
             patch('backend.api.routes.web_form.db') as mock_db:

            mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
            mock_conv_repo.create = AsyncMock(return_value=mock_conversation)
            mock_ticket_repo.create = AsyncMock(return_value=mock_ticket)
            mock_queue.publish = AsyncMock()

            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            xss_data = {
                "name": "John<script>alert('xss')</script>Doe",
                "email": "john@example.com",
                "subject": "Test<script>alert('xss')</script>Subject",
                "category": "general",
                "priority": "medium",
                "message": "Message with <script>alert('xss')</script> malicious code"
            }

            response = client.post("/support/submit", json=xss_data)

            # Should succeed but with sanitized data
            assert response.status_code == 200

            # Verify queue was called with sanitized data
            mock_queue.publish.assert_called_once()
            call_args = mock_queue.publish.call_args
            message = call_args[1]['message']

            # Check that script tags were removed
            assert '<script>' not in message['message']['content']
            assert '<script>' not in message['message']['subject']

    def test_submit_form_message_too_short(self, client):
        """Test form submission with message that's too short."""
        short_message_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test subject",
            "category": "general",
            "priority": "medium",
            "message": "Short"  # Less than 10 characters
        }

        response = client.post("/support/submit", json=short_message_data)
        # Returns 400 because custom validation catches it after sanitization
        assert response.status_code == 400
        assert "Invalid message content" in response.json()["detail"]

    def test_submit_form_invalid_category(self, client):
        """Test form submission with invalid category."""
        invalid_category_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test subject",
            "category": "invalid_category",
            "priority": "medium",
            "message": "This is a test message with enough characters."
        }

        response = client.post("/support/submit", json=invalid_category_data)
        assert response.status_code == 422

    def test_submit_form_invalid_priority(self, client):
        """Test form submission with invalid priority."""
        invalid_priority_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test subject",
            "category": "general",
            "priority": "invalid_priority",
            "message": "This is a test message with enough characters."
        }

        response = client.post("/support/submit", json=invalid_priority_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_form_always_creates_new_conversation(self, client, mock_customer, mock_conversation, mock_ticket):
        """Test that a new conversation is created even if one already exists."""
        with patch('backend.api.routes.web_form.customer_repo') as mock_customer_repo, \
             patch('backend.api.routes.web_form.conversation_repo') as mock_conv_repo, \
             patch('backend.api.routes.web_form.ticket_repo') as mock_ticket_repo, \
             patch('backend.api.routes.web_form.queue_client') as mock_queue, \
             patch('backend.api.routes.web_form.db') as mock_db:

            mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
            mock_conv_repo.create = AsyncMock(return_value=mock_conversation)
            mock_ticket_repo.create = AsyncMock(return_value=mock_ticket)
            mock_queue.publish = AsyncMock()

            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            form_data = {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Follow-up question",
                "category": "general",
                "priority": "medium",
                "message": "I have another question about my previous issue."
            }

            response = client.post("/support/submit", json=form_data)

            assert response.status_code == 200

            # Verify a new conversation AND ticket were created
            mock_conv_repo.create.assert_called_once()
            mock_ticket_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_form_database_error(self, client):
        """Test handling of database errors."""
        with patch('backend.api.routes.web_form.customer_repo') as mock_customer_repo:
            # Simulate database error
            mock_customer_repo.find_or_create = AsyncMock(side_effect=Exception("Database connection failed"))

            form_data = {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Test subject",
                "category": "general",
                "priority": "medium",
                "message": "This is a test message with enough characters."
            }

            response = client.post("/support/submit", json=form_data)

            assert response.status_code == 500
            assert "error" in response.json() or "detail" in response.json()

    def test_submit_form_with_phone_number(self, client, mock_customer, mock_conversation, mock_ticket):
        """Test form submission with optional phone number."""
        with patch('backend.api.routes.web_form.customer_repo') as mock_customer_repo, \
             patch('backend.api.routes.web_form.conversation_repo') as mock_conv_repo, \
             patch('backend.api.routes.web_form.ticket_repo') as mock_ticket_repo, \
             patch('backend.api.routes.web_form.queue_client') as mock_queue, \
             patch('backend.api.routes.web_form.db') as mock_db:

            mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
            mock_conv_repo.create = AsyncMock(return_value=mock_conversation)
            mock_ticket_repo.create = AsyncMock(return_value=mock_ticket)
            mock_queue.publish = AsyncMock()

            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            form_data = {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "subject": "Test with phone",
                "category": "general",
                "priority": "medium",
                "message": "This is a test message with phone number included."
            }

            response = client.post("/support/submit", json=form_data)

            assert response.status_code == 200

            # Verify phone was passed to customer creation
            mock_customer_repo.find_or_create.assert_called_once()
            call_kwargs = mock_customer_repo.find_or_create.call_args[1]
            assert 'phone' in call_kwargs
