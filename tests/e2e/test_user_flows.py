"""End-to-end tests for critical user flows.

These tests validate complete workflows from API request through
worker processing to final response.
"""

import pytest
import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from backend.worker.message_processor import MessageProcessor
from backend.db.repositories.customer_repo import customer_repo
from backend.db.repositories.conversation_repo import conversation_repo
from backend.db.repositories.ticket_repo import ticket_repo


@pytest.mark.e2e
class TestWebFormE2EFlow:
    """End-to-end tests for web form submission flow."""

    @pytest.mark.asyncio
    async def test_complete_web_form_flow(self):
        """
        Test complete flow: Form submission → Queue → AI processing → Response.

        Flow:
        1. Customer submits web form
        2. Customer/conversation/ticket created
        3. Message queued
        4. Worker processes message
        5. AI generates response
        6. Response saved to database
        """
        with patch('backend.worker.ai_agent.ai_agent') as mock_ai, \
             patch('backend.integrations.queue_client.queue_client') as mock_queue, \
             patch('backend.db.connection.db') as mock_db:

            # Mock AI response
            mock_ai.generate_response = AsyncMock(
                return_value=("Thank you for contacting us. How can I help?", 50, 0.9)
            )

            # Mock database
            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Create processor
            processor = MessageProcessor()

            # Simulate web form message
            message = {
                "type": "support_request",
                "ticket_id": str(uuid4()),
                "conversation_id": str(uuid4()),
                "customer_id": str(uuid4()),
                "channel": "web_form",
                "message": {
                    "role": "customer",
                    "content": "I need help with my account",
                    "subject": "Account Help",
                    "category": "technical",
                    "priority": "medium"
                },
                "customer": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": None
                }
            }

            # Process message
            await processor.process_support_request(message)

            # Verify AI was called
            mock_ai.generate_response.assert_called_once()
            call_args = mock_ai.generate_response.call_args
            assert call_args[1]['message'] == "I need help with my account"
            assert call_args[1]['channel'] == "web_form"

    @pytest.mark.asyncio
    async def test_web_form_with_escalation(self):
        """
        Test web form flow with escalation trigger.

        Flow:
        1. Customer submits form with escalation keyword
        2. Escalation detected
        3. Ticket escalated
        4. Escalation message sent
        """
        with patch('backend.worker.escalation.escalation_detector') as mock_escalation, \
             patch('backend.worker.ticket_service.ticket_service') as mock_ticket_service, \
             patch('backend.db.connection.db') as mock_db:

            # Mock escalation detection
            mock_escalation.detect_escalation = MagicMock(
                return_value=(True, "Pricing inquiry detected", ["pricing", "cost"])
            )

            mock_ticket_service.escalate_ticket = AsyncMock()
            mock_ticket_service.add_message = AsyncMock()

            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            processor = MessageProcessor()

            message = {
                "type": "support_request",
                "ticket_id": str(uuid4()),
                "conversation_id": str(uuid4()),
                "customer_id": str(uuid4()),
                "channel": "web_form",
                "message": {
                    "role": "customer",
                    "content": "What is the pricing for your enterprise plan?",
                    "subject": "Pricing Question",
                    "category": "billing",
                    "priority": "high"
                },
                "customer": {
                    "name": "Jane Smith",
                    "email": "jane@example.com"
                }
            }

            await processor.process_support_request(message)

            # Verify escalation was triggered
            mock_ticket_service.escalate_ticket.assert_called_once()


@pytest.mark.e2e
class TestWhatsAppE2EFlow:
    """End-to-end tests for WhatsApp message flow."""

    @pytest.mark.asyncio
    async def test_complete_whatsapp_flow(self):
        """
        Test complete WhatsApp flow: Message received → AI response → WhatsApp sent.

        Flow:
        1. WhatsApp message received
        2. Customer found/created
        3. Conversation created/reused
        4. AI generates response
        5. Response sent via WhatsApp
        """
        with patch('backend.worker.ai_agent.ai_agent') as mock_ai, \
             patch('backend.integrations.whatsapp_client.whatsapp_client') as mock_whatsapp, \
             patch('backend.db.connection.db') as mock_db:

            # Mock AI response
            mock_ai.generate_response = AsyncMock(
                return_value=("Hi! How can I help you today?", 30, 0.85)
            )

            # Mock WhatsApp client
            mock_whatsapp.send_text_message = AsyncMock(
                return_value={"message_id": "wamid.123456"}
            )

            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            processor = MessageProcessor()

            # Simulate WhatsApp message
            message = {
                "type": "whatsapp_message",
                "from_phone": "+1234567890",
                "content": "Hello, I need support",
                "message_id": "wamid.incoming123"
            }

            await processor.process_support_request(message)

            # Verify WhatsApp response was sent
            mock_whatsapp.send_text_message.assert_called_once()
            call_args = mock_whatsapp.send_text_message.call_args
            assert call_args[1]['to_phone'] == "+1234567890"
            assert "help" in call_args[1]['message'].lower()


@pytest.mark.e2e
class TestCrossChannelE2EFlow:
    """End-to-end tests for cross-channel conversation continuity."""

    @pytest.mark.asyncio
    async def test_cross_channel_conversation_continuity(self):
        """
        Test conversation continuity across channels.

        Flow:
        1. Customer submits web form
        2. Customer sends WhatsApp message
        3. Same conversation is reused
        4. AI has context from previous channel
        """
        with patch('backend.worker.ai_agent.ai_agent') as mock_ai, \
             patch('backend.db.repositories.customer_repo.customer_repo') as mock_customer_repo, \
             patch('backend.db.repositories.conversation_repo.conversation_repo') as mock_conv_repo, \
             patch('backend.db.connection.db') as mock_db:

            # Mock customer (same across channels)
            mock_customer = MagicMock()
            mock_customer.id = uuid4()
            mock_customer.email = "john@example.com"
            mock_customer.phone = "+1234567890"

            # Mock conversation (reused)
            mock_conversation = MagicMock()
            mock_conversation.id = uuid4()

            mock_customer_repo.find_or_create = AsyncMock(return_value=mock_customer)
            mock_conv_repo.get_active_by_customer = AsyncMock(return_value=mock_conversation)
            mock_conv_repo.get_messages = AsyncMock(return_value=[
                {"role": "customer", "content": "I need help with billing"},
                {"role": "agent", "content": "I can help with that"}
            ])

            mock_ai.generate_response = AsyncMock(
                return_value=("Continuing from our previous conversation...", 40, 0.9)
            )

            mock_conn = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            processor = MessageProcessor()

            # First message via web form
            web_message = {
                "type": "support_request",
                "ticket_id": str(uuid4()),
                "conversation_id": str(mock_conversation.id),
                "customer_id": str(mock_customer.id),
                "channel": "web_form",
                "message": {"content": "I need help with billing"},
                "customer": {"email": "john@example.com"}
            }

            await processor.process_support_request(web_message)

            # Second message via WhatsApp (same customer)
            whatsapp_message = {
                "type": "whatsapp_message",
                "from_phone": "+1234567890",
                "content": "Can you send me an invoice?",
                "message_id": "wamid.123"
            }

            await processor.process_support_request(whatsapp_message)

            # Verify conversation history was loaded
            mock_conv_repo.get_messages.assert_called()

            # Verify AI received conversation history
            ai_calls = mock_ai.generate_response.call_args_list
            assert len(ai_calls) >= 1
            # Check that conversation_history was passed
            last_call = ai_calls[-1]
            assert 'conversation_history' in last_call[1]


@pytest.mark.e2e
class TestMessageDeduplicationE2E:
    """End-to-end tests for message deduplication."""

    @pytest.mark.asyncio
    async def test_duplicate_whatsapp_message_ignored(self):
        """
        Test that duplicate WhatsApp messages are ignored.

        Flow:
        1. WhatsApp message received
        2. Message processed
        3. Same message received again (webhook retry)
        4. Duplicate detected and ignored
        """
        with patch('backend.db.connection.db') as mock_db:

            mock_conn = AsyncMock()

            # First call: message not processed yet
            # Second call: message already processed
            mock_conn.fetchval = AsyncMock(side_effect=[False, True])
            mock_conn.execute = AsyncMock()

            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            processor = MessageProcessor()

            message = {
                "type": "whatsapp_message",
                "from_phone": "+1234567890",
                "content": "Hello",
                "message_id": "wamid.duplicate123"
            }

            # First processing - should succeed
            await processor.process_support_request(message)

            # Second processing - should be skipped
            await processor.process_support_request(message)

            # Verify deduplication check was called twice
            assert mock_conn.fetchval.call_count == 2
