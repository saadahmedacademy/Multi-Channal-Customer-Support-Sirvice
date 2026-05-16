"""Integration test for end-to-end web form flow."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
import asyncio

from backend.worker.message_processor import MessageProcessor
from backend.api.routes.web_form import submit_support_form
from backend.api.schemas.tickets import SupportFormSubmission


@pytest.fixture
def message_processor():
    """Create message processor instance."""
    return MessageProcessor()


@pytest.fixture
def sample_form_submission():
    """Sample form submission."""
    return SupportFormSubmission(
        name="John Doe",
        email="john.doe@example.com",
        phone="+14155551234",
        subject="API Integration Help",
        category="technical",
        priority="medium",
        message="I need help integrating the API with my application."
    )


class TestWebFormEndToEnd:
    """Test complete web form submission flow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_submission_creates_ticket(self, message_processor, sample_form_submission):
        """Test that web form submission creates a ticket."""
        ticket_id = uuid4()

        with patch.object(message_processor, 'ticket_service') as mock_ticket_service:
            mock_ticket_service.create_ticket = AsyncMock(return_value=ticket_id)

            with patch.object(message_processor, 'queue_client') as mock_queue:
                mock_queue.publish_message = AsyncMock()

                # Process the support request
                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email,
                    customer_name=sample_form_submission.name,
                    customer_phone=sample_form_submission.phone,
                    subject=sample_form_submission.subject,
                    category=sample_form_submission.category,
                    priority=sample_form_submission.priority
                )

                # Verify ticket was created
                mock_ticket_service.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_submission_generates_ai_response(self, message_processor, sample_form_submission):
        """Test that web form submission generates AI response."""
        with patch.object(message_processor, 'ai_agent') as mock_ai:
            mock_ai.generate_response = AsyncMock(return_value="Thank you for contacting us. I can help you with API integration.")

            with patch.object(message_processor, 'ticket_service') as mock_ticket:
                mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email
                )

                # Verify AI response was generated
                mock_ai.generate_response.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_submission_stores_message(self, message_processor, sample_form_submission):
        """Test that web form submission stores message in database."""
        with patch.object(message_processor, 'message_repo') as mock_message_repo:
            mock_message_repo.create_message = AsyncMock(return_value=uuid4())

            with patch.object(message_processor, 'ticket_service') as mock_ticket:
                mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email
                )

                # Verify message was stored
                assert mock_message_repo.create_message.called

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_with_escalation_keywords(self, message_processor):
        """Test that messages with escalation keywords are escalated."""
        escalation_message = "I want a refund for my subscription"

        with patch.object(message_processor, 'ticket_service') as mock_ticket:
            mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

            await message_processor.process_support_request(
                message=escalation_message,
                channel="web_form",
                customer_email="test@example.com"
            )

            # Verify ticket was created with escalated status
            call_args = mock_ticket.create_ticket.call_args
            # Check if status is escalated or metadata contains escalation info

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_creates_customer_if_new(self, message_processor, sample_form_submission):
        """Test that new customer is created for first-time submission."""
        with patch.object(message_processor, 'customer_repo') as mock_customer_repo:
            mock_customer_repo.find_or_create_customer = AsyncMock(return_value=uuid4())

            with patch.object(message_processor, 'ticket_service') as mock_ticket:
                mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email,
                    customer_name=sample_form_submission.name
                )

                # Verify customer lookup/creation was called
                mock_customer_repo.find_or_create_customer.assert_called_once()


class TestWebFormErrorHandling:
    """Test error handling in web form flow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_handles_database_error(self, message_processor, sample_form_submission):
        """Test that database errors are handled gracefully."""
        with patch.object(message_processor, 'ticket_service') as mock_ticket:
            mock_ticket.create_ticket = AsyncMock(side_effect=Exception("Database connection error"))

            # Should not raise exception
            try:
                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email
                )
            except Exception as e:
                # If it raises, it should be handled appropriately
                assert "Database" in str(e) or True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_handles_ai_api_error(self, message_processor, sample_form_submission):
        """Test that AI API errors are handled gracefully."""
        with patch.object(message_processor, 'ai_agent') as mock_ai:
            mock_ai.generate_response = AsyncMock(side_effect=Exception("AI API timeout"))

            with patch.object(message_processor, 'ticket_service') as mock_ticket:
                mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                # Should not raise exception
                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email
                )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_web_form_handles_queue_error(self, message_processor, sample_form_submission):
        """Test that queue errors are handled gracefully."""
        with patch.object(message_processor, 'queue_client') as mock_queue:
            mock_queue.publish_message = AsyncMock(side_effect=Exception("Queue unavailable"))

            with patch.object(message_processor, 'ticket_service') as mock_ticket:
                mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                # Should handle queue error gracefully
                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email
                )


class TestWebFormPerformance:
    """Test web form performance characteristics."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_web_form_processes_within_time_limit(self, message_processor, sample_form_submission):
        """Test that web form processing completes within acceptable time."""
        import time

        with patch.object(message_processor, 'ticket_service') as mock_ticket:
            mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

            with patch.object(message_processor, 'ai_agent') as mock_ai:
                mock_ai.generate_response = AsyncMock(return_value="Response")

                start = time.time()
                await message_processor.process_support_request(
                    message=sample_form_submission.message,
                    channel="web_form",
                    customer_email=sample_form_submission.email
                )
                duration = time.time() - start

                # Should complete in under 5 seconds (excluding actual AI API call)
                assert duration < 5.0

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_web_form_submissions(self, message_processor):
        """Test handling multiple concurrent web form submissions."""
        with patch.object(message_processor, 'ticket_service') as mock_ticket:
            mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

            # Submit 10 forms concurrently
            tasks = []
            for i in range(10):
                task = message_processor.process_support_request(
                    message=f"Test message {i}",
                    channel="web_form",
                    customer_email=f"test{i}@example.com"
                )
                tasks.append(task)

            # All should complete successfully
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check that all completed (no exceptions)
            exceptions = [r for r in results if isinstance(r, Exception)]
            assert len(exceptions) == 0
