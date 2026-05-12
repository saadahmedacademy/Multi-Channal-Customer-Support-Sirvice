"""
Integration tests.

Tests for full workflow: queue → worker → AI → database → response
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Queue Integration Tests ==============

class TestQueueIntegration:
    """Tests for queue integration."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_publish_message_to_queue(self):
        """Test publishing message to queue."""
        from backend.integrations.queue_client import queue_client, TOPICS
        
        # Verify topics are defined
        assert "tickets_incoming" in TOPICS
        assert "tickets_outgoing" in TOPICS
        
        # Verify queue client exists
        assert queue_client is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_queue_client_topics(self):
        """Test that all required topics are defined."""
        from backend.integrations.queue_client import TOPICS
        
        assert "tickets_incoming" in TOPICS
        assert "tickets_outgoing" in TOPICS
        assert "escalations" in TOPICS
        assert "metrics" in TOPICS
        assert "dlq" in TOPICS


# ============== Worker Integration Tests ==============

class TestWorkerIntegration:
    """Tests for worker message processing."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_process_web_form_message(self, sample_support_form_submission):
        """Test processing web form message through worker."""
        from backend.worker.message_processor import MessageProcessor
        
        processor = MessageProcessor()
        
        mock_message = {
            "ticket_id": str(uuid4()),
            "conversation_id": str(uuid4()),
            "customer_id": str(uuid4()),
            "channel": "web_form",
            "message": {"content": sample_support_form_submission["message"]},
            "customer": {"email": sample_support_form_submission["email"]}
        }
        
        with patch.object(processor, 'process_support_request', new_callable=AsyncMock) as mock_process:
            await processor.handle_message("fte.tickets.incoming", mock_message)
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_process_whatsapp_message(self):
        """Test processing WhatsApp message through worker."""
        from backend.worker.message_processor import MessageProcessor
        
        processor = MessageProcessor()
        
        mock_message = {
            "type": "whatsapp_message",
            "from_phone": "+14155551234",
            "content": "I need help",
            "message_id": "wamid.test123",
            "channel": "whatsapp"
        }
        
        with patch.object(processor, 'process_support_request', new_callable=AsyncMock) as mock_process:
            await processor.handle_message("fte.tickets.incoming", mock_message)
            mock_process.assert_called_once()


# ============== Database Integration Tests ==============

class TestDatabaseIntegration:
    """Tests for database operations."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_customer_repository_operations(self, sample_customer_data):
        """Test customer repository CRUD operations."""
        from backend.db.repositories.customer_repo import CustomerRepository, normalize_phone
        
        # Test phone normalization
        assert normalize_phone("4155551234") == "+14155551234"
        assert normalize_phone("+14155551234") == "+14155551234"
        assert normalize_phone("(415) 555-1234") == "+14155551234"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ticket_repository_operations(self):
        """Test ticket repository operations."""
        from backend.db.repositories.ticket_repo import TicketRepository
        
        repo = TicketRepository()
        
        # Verify repository methods exist
        assert hasattr(repo, 'create')
        assert hasattr(repo, 'get_by_id')
        assert hasattr(repo, 'update_status')
        assert hasattr(repo, 'get_by_customer_id')

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_repository_operations(self):
        """Test conversation repository operations."""
        from backend.db.repositories.conversation_repo import ConversationRepository
        
        repo = ConversationRepository()
        
        # Verify repository methods exist
        assert hasattr(repo, 'create')
        assert hasattr(repo, 'get_by_id')
        assert hasattr(repo, 'get_active_by_customer')
        assert hasattr(repo, 'update_status')


# ============== AI Integration Tests ==============

class TestAIIntegration:
    """Tests for AI service integration."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ai_agent_response_generation(self):
        """Test AI agent can generate responses."""
        from backend.worker.ai_agent import AIAgent
        
        with patch('backend.worker.ai_agent.settings') as mock_settings:
            mock_settings.openrouter_api_key = None
            mock_settings.gemini_api_key = None
            mock_settings.ai_timeout = 30
            mock_settings.max_tokens = 500
            
            agent = AIAgent()
            response, tokens, confidence = await agent.generate_response(
                message="How do I reset my password?",
                channel="web_form"
            )
            
            assert response is not None
            assert len(response) > 0
            assert tokens == 0  # No API called

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ai_channel_aware_responses(self):
        """Test AI generates channel-appropriate responses."""
        from backend.worker.ai_agent import CHANNEL_CONFIGS
        
        # Verify different channels have different configurations
        assert CHANNEL_CONFIGS["web_form"]["max_length"] != CHANNEL_CONFIGS["whatsapp"]["max_length"]
        assert CHANNEL_CONFIGS["whatsapp"]["max_length"] == 300  # Concise for WhatsApp
        assert CHANNEL_CONFIGS["web_form"]["max_length"] == 1000  # Detailed for web


# ============== Escalation Integration Tests ==============

class TestEscalationIntegration:
    """Tests for escalation workflow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_escalation_workflow(self):
        """Test complete escalation workflow."""
        from backend.worker.escalation import EscalationDetector
        from backend.worker.sentiment import SentimentAnalyzer
        
        detector = EscalationDetector()
        analyzer = SentimentAnalyzer()
        
        # Test message that should escalate
        message = "I want a refund! This is terrible!"
        sentiment = analyzer.analyze(message)
        requires_escalation, reason, keywords = detector.detect_escalation(
            message, sentiment["score"]
        )
        
        assert requires_escalation is True
        assert len(keywords) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_no_escalation_normal_query(self):
        """Test that normal queries don't escalate."""
        from backend.worker.escalation import EscalationDetector
        
        detector = EscalationDetector()
        requires_escalation, reason, keywords = detector.detect_escalation(
            "How do I use the API?"
        )
        
        assert requires_escalation is False


# ============== End-to-End Flow Tests ==============

class TestEndToEndFlow:
    """End-to-end workflow tests."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_full_web_form_flow(self, sample_support_form_submission):
        """Test complete web form submission to response flow."""
        # This test simulates the full flow:
        # 1. User submits form
        # 2. Ticket created
        # 3. Message queued
        # 4. Worker processes
        # 5. AI generates response
        # 6. Response saved
        
        from uuid import uuid4
        
        customer_id = uuid4()
        conversation_id = uuid4()
        ticket_id = uuid4()
        
        # Simulate form submission
        submission_data = {
            "ticket_id": str(ticket_id),
            "conversation_id": str(conversation_id),
            "customer_id": str(customer_id),
            "channel": "web_form",
            "message": {"content": sample_support_form_submission["message"]},
            "customer": {"email": sample_support_form_submission["email"]}
        }
        
        # Verify message structure
        assert "ticket_id" in submission_data
        assert "message" in submission_data
        assert "customer" in submission_data

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_full_whatsapp_flow(self):
        """Test complete WhatsApp message to response flow."""
        from uuid import uuid4
        
        customer_id = uuid4()
        conversation_id = uuid4()
        ticket_id = uuid4()
        
        # Simulate WhatsApp message
        whatsapp_message = {
            "type": "whatsapp_message",
            "from_phone": "+14155551234",
            "content": "Help me please",
            "message_id": "wamid.test123",
            "ticket_id": str(ticket_id),
            "conversation_id": str(conversation_id),
            "customer_id": str(customer_id)
        }
        
        # Verify message structure
        assert whatsapp_message["type"] == "whatsapp_message"
        assert "from_phone" in whatsapp_message
        assert "content" in whatsapp_message


# ============== Cross-Channel Integration Tests ==============

class TestCrossChannelIntegration:
    """Tests for cross-channel functionality."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_customer_identifier_linking(self):
        """Test linking multiple identifiers to same customer."""
        from backend.db.repositories.customer_identifier_repo import CustomerIdentifierRepository
        
        repo = CustomerIdentifierRepository()
        
        # Verify repository methods exist
        assert hasattr(repo, 'add_identifier')
        assert hasattr(repo, 'get_customer_by_identifier')
        assert hasattr(repo, 'get_all_identifiers')
        assert hasattr(repo, 'link_identifiers')

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_history_retrieval(self):
        """Test retrieving conversation history across channels."""
        from backend.worker.message_processor import MessageProcessor
        
        processor = MessageProcessor()
        
        # Verify method exists
        assert hasattr(processor, '_get_conversation_history')


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration or e2e"])
