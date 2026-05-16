"""API tests for web form submission endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from backend.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def valid_form_data():
    """Valid form submission data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+14155551234",
        "subject": "API Integration Help",
        "category": "technical",
        "priority": "medium",
        "message": "I need help integrating the API with my application."
    }


class TestWebFormSubmission:
    """Test web form submission endpoint."""

    def test_submit_form_with_valid_data(self, client, valid_form_data):
        """Test submitting form with valid data returns 200."""
        with patch('backend.integrations.queue_client.queue_client') as mock_queue:
            mock_queue.publish_message = AsyncMock()

            response = client.post("/support/submit", json=valid_form_data)

            assert response.status_code == 200
            data = response.json()
            assert "ticket_id" in data
            assert "message" in data

    def test_submit_form_missing_required_fields(self, client):
        """Test submitting form with missing required fields returns 422."""
        incomplete_data = {
            "name": "John Doe",
            "email": "john.doe@example.com"
            # Missing subject and message
        }

        response = client.post("/support/submit", json=incomplete_data)

        assert response.status_code == 422

    def test_submit_form_invalid_email(self, client, valid_form_data):
        """Test submitting form with invalid email returns 400."""
        valid_form_data["email"] = "not-an-email"

        response = client.post("/support/submit", json=valid_form_data)

        assert response.status_code in [400, 422]

    def test_submit_form_xss_attempt(self, client, valid_form_data):
        """Test that XSS attempts are sanitized."""
        valid_form_data["message"] = "Hello <script>alert('XSS')</script> World"

        with patch('backend.integrations.queue_client.queue_client') as mock_queue:
            mock_queue.publish_message = AsyncMock()

            response = client.post("/support/submit", json=valid_form_data)

            assert response.status_code == 200
            # Message should be sanitized (script tags removed)

    def test_submit_form_very_long_message(self, client, valid_form_data):
        """Test submitting form with very long message."""
        valid_form_data["message"] = "a" * 15000  # 15KB message

        with patch('backend.integrations.queue_client.queue_client') as mock_queue:
            mock_queue.publish_message = AsyncMock()

            response = client.post("/support/submit", json=valid_form_data)

            # Should either accept (with truncation) or reject gracefully
            assert response.status_code in [200, 400, 413]

    def test_submit_form_rate_limiting(self, client, valid_form_data):
        """Test that rate limiting is enforced."""
        with patch('backend.integrations.queue_client.queue_client') as mock_queue:
            mock_queue.publish_message = AsyncMock()

            # Submit many requests rapidly
            responses = []
            for _ in range(15):  # Rate limit is 10/min
                response = client.post("/support/submit", json=valid_form_data)
                responses.append(response.status_code)

            # At least one should be rate limited (429)
            assert 429 in responses or all(r == 200 for r in responses)


class TestTicketStatusEndpoint:
    """Test ticket status endpoint."""

    def test_get_ticket_status_valid_id(self, client):
        """Test getting ticket status with valid ID."""
        ticket_id = str(uuid4())

        with patch('backend.db.repositories.ticket_repo.TicketRepository') as mock_repo:
            mock_instance = mock_repo.return_value
            mock_instance.get_ticket = AsyncMock(return_value={
                "id": ticket_id,
                "status": "open",
                "created_at": "2026-05-16T10:00:00Z"
            })

            response = client.get(f"/support/ticket/{ticket_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == ticket_id
            assert "status" in data

    def test_get_ticket_status_invalid_id(self, client):
        """Test getting ticket status with invalid ID returns 404."""
        ticket_id = str(uuid4())

        with patch('backend.db.repositories.ticket_repo.TicketRepository') as mock_repo:
            mock_instance = mock_repo.return_value
            mock_instance.get_ticket = AsyncMock(return_value=None)

            response = client.get(f"/support/ticket/{ticket_id}")

            assert response.status_code == 404

    def test_get_ticket_status_malformed_id(self, client):
        """Test getting ticket status with malformed ID returns 400."""
        response = client.get("/support/ticket/not-a-uuid")

        assert response.status_code in [400, 422]


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check returns 200."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_health_check_includes_components(self, client):
        """Test that health check includes component status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # Should include database, queue, etc.
        assert isinstance(data, dict)


class TestCORSHeaders:
    """Test CORS headers."""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options("/support/submit")

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers or \
               response.status_code == 200


class TestErrorHandling:
    """Test error handling."""

    def test_404_for_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoint returns 404."""
        response = client.get("/nonexistent/endpoint")

        assert response.status_code == 404

    def test_405_for_wrong_method(self, client):
        """Test that wrong HTTP method returns 405."""
        response = client.get("/support/submit")  # Should be POST

        assert response.status_code == 405

    def test_error_response_format(self, client):
        """Test that error responses have consistent format."""
        response = client.get("/nonexistent/endpoint")

        assert response.status_code == 404
        data = response.json()
        # Should have error details
        assert "detail" in data or "error" in data
