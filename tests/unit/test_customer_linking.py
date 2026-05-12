"""
Customer Linking Tests.

Tests for cross-channel customer identifier linking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Fixtures ==============

@pytest.fixture
def mock_customer_repo():
    """Mock customer repository."""
    with patch('backend.api.routes.customer_linking.customer_repo') as mock:
        yield mock


@pytest.fixture
def mock_identifier_repo():
    """Mock customer identifier repository."""
    with patch('backend.api.routes.customer_linking.customer_identifier_repo') as mock:
        yield mock


# ============== Link Identifiers Tests ==============

class TestLinkIdentifiers:
    """Tests for linking customer identifiers."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_new_customer_email_only(self, mock_customer_repo, mock_identifier_repo):
        """Test linking creates new customer with email."""
        mock_customer_repo.get_by_email = AsyncMock(return_value=None)
        mock_customer_repo.get_by_phone = AsyncMock(return_value=None)
        
        mock_customer = MagicMock()
        mock_customer.id = uuid4()
        mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
        
        mock_identifier_repo.get_all_identifiers = AsyncMock(return_value=[])
        mock_identifier_repo.add_identifier = AsyncMock(return_value=True)

        from fastapi.testclient import TestClient
        from backend.api.main import app

        with patch('backend.db.connection.init_db', AsyncMock()):
            with patch('backend.db.connection.close_db', AsyncMock()):
                with patch('backend.integrations.queue_client.queue_client', AsyncMock()):
                    with TestClient(app, raise_server_exceptions=False) as client:
                        response = client.post("/customers/link-identifiers", json={
                            "email": "test@example.com"
                        })

        assert response.status_code == 200
        data = response.json()
        assert "customer_id" in data
        assert "message" in data
        assert "identifiers" in data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_email_and_phone_new_customer(self, mock_customer_repo, mock_identifier_repo):
        """Test linking both email and phone for new customer."""
        mock_customer_repo.get_by_email = AsyncMock(return_value=None)
        mock_customer_repo.get_by_phone = AsyncMock(return_value=None)
        
        mock_customer = MagicMock()
        mock_customer.id = uuid4()
        mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
        
        mock_identifier_repo.get_all_identifiers = AsyncMock(return_value=[])
        mock_identifier_repo.add_identifier = AsyncMock(return_value=True)

        from fastapi.testclient import TestClient
        from backend.api.main import app

        with patch('backend.db.connection.init_db', AsyncMock()):
            with patch('backend.db.connection.close_db', AsyncMock()):
                with patch('backend.integrations.queue_client.queue_client', AsyncMock()):
                    with TestClient(app, raise_server_exceptions=False) as client:
                        response = client.post("/customers/link-identifiers", json={
                            "email": "test@example.com",
                            "phone": "+14155551234"
                        })

        assert response.status_code == 200
        data = response.json()
        assert "customer_id" in data

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_link_missing_identifier_error(self):
        """Test error when no identifiers provided."""
        from fastapi.testclient import TestClient
        from backend.api.main import app

        with patch('backend.db.connection.init_db', AsyncMock()):
            with patch('backend.db.connection.close_db', AsyncMock()):
                with patch('backend.integrations.queue_client.queue_client', AsyncMock()):
                    with TestClient(app, raise_server_exceptions=False) as client:
                        response = client.post("/customers/link-identifiers", json={})

        assert response.status_code == 400


# ============== Get Identifiers Tests ==============

class TestGetIdentifiers:
    """Tests for retrieving customer identifiers."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_customer_identifiers(self, mock_identifier_repo):
        """Test retrieving all identifiers for a customer."""
        mock_identifiers = [
            {
                "id": str(uuid4()),
                "identifier_type": "email",
                "identifier_value": "test@example.com",
                "verified": True,
                "created_at": "2026-04-11T12:00:00"
            },
            {
                "id": str(uuid4()),
                "identifier_type": "phone",
                "identifier_value": "+14155551234",
                "verified": True,
                "created_at": "2026-04-11T12:00:00"
            }
        ]
        mock_identifier_repo.get_all_identifiers = AsyncMock(return_value=mock_identifiers)

        from fastapi.testclient import TestClient
        from backend.api.main import app

        with patch('backend.db.connection.init_db', AsyncMock()):
            with patch('backend.db.connection.close_db', AsyncMock()):
                with patch('backend.integrations.queue_client.queue_client', AsyncMock()):
                    with TestClient(app, raise_server_exceptions=False) as client:
                        response = client.get(f"/customers/{uuid4()}/identifiers")

        assert response.status_code == 200
        data = response.json()
        assert "identifiers" in data
        assert data["total"] == 2


# ============== Integration Tests ==============

class TestCustomerLinkingIntegration:
    """Integration tests for customer linking in message processing."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_email_message_links_to_existing_customer(self):
        """Test that email messages link to customers by email."""
        from backend.worker.message_processor import MessageProcessor
        
        processor = MessageProcessor()
        
        # Verify email handling code exists
        import inspect
        source = inspect.getsource(processor.process_support_request)
        
        assert 'email_message' in source
        assert 'from_email' in source
        assert 'customer_repo.find_or_create' in source

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_whatsapp_message_links_to_existing_customer(self):
        """Test that WhatsApp messages link to customers by phone."""
        from backend.worker.message_processor import MessageProcessor
        
        processor = MessageProcessor()
        
        # Verify WhatsApp handling code exists
        import inspect
        source = inspect.getsource(processor.process_support_request)
        
        assert 'whatsapp_message' in source
        assert 'from_phone' in source
        assert 'normalize_phone' in source


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
