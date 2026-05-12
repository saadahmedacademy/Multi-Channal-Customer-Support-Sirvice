"""
Test configuration and fixtures for AI Customer Support Agent.

Provides shared fixtures, mocks, and utilities for all tests.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============== Test Data Fixtures ==============

@pytest.fixture
def sample_customer_data() -> Dict[str, Any]:
    """Sample customer data for testing."""
    return {
        "id": uuid4(),
        "email": "test@example.com",
        "phone": "+14155551234",
        "name": "Test User",
        "created_at": datetime.utcnow(),
        "metadata": {"timezone": "America/New_York", "language": "en"}
    }


@pytest.fixture
def sample_conversation_data(sample_customer_data) -> Dict[str, Any]:
    """Sample conversation data for testing."""
    return {
        "id": uuid4(),
        "customer_id": sample_customer_data["id"],
        "initial_channel": "web_form",
        "started_at": datetime.utcnow(),
        "status": "active",
        "metadata": {}
    }


@pytest.fixture
def sample_ticket_data(sample_customer_data, sample_conversation_data) -> Dict[str, Any]:
    """Sample ticket data for testing."""
    return {
        "id": uuid4(),
        "conversation_id": sample_conversation_data["id"],
        "customer_id": sample_customer_data["id"],
        "source_channel": "web_form",
        "category": "technical",
        "priority": "medium",
        "status": "open",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def sample_message_data(sample_conversation_data) -> Dict[str, Any]:
    """Sample message data for testing."""
    return {
        "id": uuid4(),
        "conversation_id": sample_conversation_data["id"],
        "channel": "web_form",
        "direction": "inbound",
        "role": "customer",
        "content": "I need help with API authentication",
        "created_at": datetime.utcnow(),
        "delivery_status": "delivered"
    }


@pytest.fixture
def sample_support_form_submission() -> Dict[str, Any]:
    """Sample web form submission data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+14155551234",
        "subject": "API Authentication Issue",
        "category": "technical",
        "priority": "medium",
        "message": "I'm having trouble authenticating with the API. Getting 401 errors."
    }


@pytest.fixture
def sample_whatsapp_message() -> Dict[str, Any]:
    """Sample WhatsApp webhook message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "1234567890"},
                    "messages": [{
                        "from": "14155551234",
                        "id": "wamid.test123",
                        "timestamp": "1234567890",
                        "type": "text",
                        "text": {"body": "I need help with my account"}
                    }]
                },
                "field": "messages"
            }]
        }]
    }


# ============== Mock Fixtures ==============

@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.execute = AsyncMock()
    return mock_conn


@pytest.fixture
def mock_db_pool(mock_db_connection):
    """Mock database connection pool."""
    mock_pool = AsyncMock()
    mock_pool.acquire = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_db_connection)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    return mock_pool


@pytest.fixture
def mock_queue_client():
    """Mock queue client."""
    mock_client = AsyncMock()
    mock_client.publish = AsyncMock()
    mock_client.start_producer = AsyncMock()
    mock_client.stop_producer = AsyncMock()
    mock_client.start_consumer = AsyncMock()
    mock_client.stop_consumer = AsyncMock()
    return mock_client


@pytest.fixture
def mock_ai_response():
    """Mock AI API response."""
    return {
        "response": "Thank you for contacting support. I'd be happy to help you with API authentication. To get an API key, please log into your dashboard and navigate to Settings > API Keys.",
        "escalation_required": False,
        "tokens_used": 150,
        "confidence": 0.95
    }


@pytest.fixture
def mock_http_client(mock_ai_response):
    """Mock HTTP client for AI API calls."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {"content": mock_ai_response["response"]}
        }],
        "usage": {"total_tokens": mock_ai_response["tokens_used"]}
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


# ============== Test Utilities ==============

@pytest.fixture
def test_event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def create_test_uuid() -> UUID:
    """Generate a test UUID."""
    return uuid4()


def create_test_timestamp() -> datetime:
    """Generate a test timestamp."""
    return datetime.utcnow()


# ============== Pytest Configuration ==============

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
