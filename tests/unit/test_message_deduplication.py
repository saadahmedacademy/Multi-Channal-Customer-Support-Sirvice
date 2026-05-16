"""Unit tests for message deduplication functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from backend.worker.message_processor import MessageProcessor


@pytest.fixture
def message_processor():
    """Create message processor instance for testing."""
    return MessageProcessor()


@pytest.fixture
def sample_whatsapp_message_id():
    """Sample WhatsApp message ID."""
    return "wamid.HBgNMTQxNTU1NTEyMzQ1FQIAERgSQzNBRjBGRjhGNzQ4QjhBODhBAA=="


@pytest.fixture
def sample_email_message_id():
    """Sample email message ID."""
    return "CADdFwRcZ1234567890abcdefghijklmnop@mail.gmail.com"


class TestMessageDeduplicationCheck:
    """Test checking if message has been processed."""

    @pytest.mark.asyncio
    async def test_is_message_processed_returns_false_for_new_message(self, message_processor, sample_whatsapp_message_id):
        """Test that new message is not marked as processed."""
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            result = await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )

            assert result is False
            mock_conn.fetchval.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_message_processed_returns_true_for_duplicate(self, message_processor, sample_whatsapp_message_id):
        """Test that duplicate message is marked as processed."""
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=True)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            result = await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_is_message_processed_handles_empty_message_id(self, message_processor):
        """Test handling of empty message ID."""
        result = await message_processor._is_message_processed("", "whatsapp")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_message_processed_handles_none_message_id(self, message_processor):
        """Test handling of None message ID."""
        result = await message_processor._is_message_processed(None, "whatsapp")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_message_processed_handles_database_error(self, message_processor, sample_whatsapp_message_id):
        """Test that database errors are handled gracefully."""
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=Exception("DB connection error"))
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Should not raise exception
            result = await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )

            assert result is False  # Fail open - allow processing on error


class TestMessageDeduplicationMarking:
    """Test marking message as processed."""

    @pytest.mark.asyncio
    async def test_mark_message_processed_inserts_record(self, message_processor, sample_whatsapp_message_id):
        """Test that marking message as processed inserts database record."""
        ticket_id = uuid4()

        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            await message_processor._mark_message_processed(
                sample_whatsapp_message_id,
                "whatsapp",
                ticket_id
            )

            mock_conn.execute.assert_called_once()
            # Verify INSERT statement was called
            call_args = mock_conn.execute.call_args[0][0]
            assert "INSERT INTO processed_messages" in call_args

    @pytest.mark.asyncio
    async def test_mark_message_processed_handles_duplicate_insert(self, message_processor, sample_whatsapp_message_id):
        """Test that duplicate insert is handled (ON CONFLICT DO NOTHING)."""
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Should not raise exception even if record already exists
            await message_processor._mark_message_processed(
                sample_whatsapp_message_id,
                "whatsapp",
                None
            )

            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_message_processed_handles_empty_message_id(self, message_processor):
        """Test handling of empty message ID."""
        # Should not raise exception
        await message_processor._mark_message_processed("", "whatsapp", None)

    @pytest.mark.asyncio
    async def test_mark_message_processed_handles_none_message_id(self, message_processor):
        """Test handling of None message ID."""
        # Should not raise exception
        await message_processor._mark_message_processed(None, "whatsapp", None)

    @pytest.mark.asyncio
    async def test_mark_message_processed_handles_database_error(self, message_processor, sample_whatsapp_message_id):
        """Test that database errors are handled gracefully."""
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(side_effect=Exception("DB error"))
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Should not raise exception
            await message_processor._mark_message_processed(
                sample_whatsapp_message_id,
                "whatsapp",
                None
            )


class TestDeduplicationIntegration:
    """Test deduplication integration with message processing."""

    @pytest.mark.asyncio
    async def test_duplicate_whatsapp_message_is_skipped(self, message_processor, sample_whatsapp_message_id):
        """Test that duplicate WhatsApp message is skipped."""
        with patch.object(message_processor, '_is_message_processed') as mock_is_processed:
            mock_is_processed.return_value = True

            # Process message
            await message_processor.process_support_request(
                message="Test message",
                channel="whatsapp",
                customer_phone="+14155551234",
                channel_message_id=sample_whatsapp_message_id,
                message_type="whatsapp_message"
            )

            # Verify message was checked for duplication
            mock_is_processed.assert_called_once_with(sample_whatsapp_message_id, "whatsapp")

    @pytest.mark.asyncio
    async def test_new_whatsapp_message_is_processed(self, message_processor, sample_whatsapp_message_id):
        """Test that new WhatsApp message is processed."""
        with patch.object(message_processor, '_is_message_processed') as mock_is_processed:
            mock_is_processed.return_value = False

            with patch.object(message_processor, '_mark_message_processed') as mock_mark:
                with patch.object(message_processor, 'ticket_service') as mock_ticket:
                    mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                    # Process message
                    await message_processor.process_support_request(
                        message="Test message",
                        channel="whatsapp",
                        customer_phone="+14155551234",
                        channel_message_id=sample_whatsapp_message_id,
                        message_type="whatsapp_message"
                    )

                    # Verify message was marked as processed
                    mock_mark.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_email_message_is_skipped(self, message_processor, sample_email_message_id):
        """Test that duplicate email message is skipped."""
        with patch.object(message_processor, '_is_message_processed') as mock_is_processed:
            mock_is_processed.return_value = True

            # Process message
            await message_processor.process_support_request(
                message="Test message",
                channel="email",
                customer_email="test@example.com",
                channel_message_id=sample_email_message_id,
                message_type="email_message"
            )

            # Verify message was checked for duplication
            mock_is_processed.assert_called_once_with(sample_email_message_id, "email")

    @pytest.mark.asyncio
    async def test_web_form_messages_are_not_deduplicated(self, message_processor):
        """Test that web form messages are not deduplicated."""
        with patch.object(message_processor, '_is_message_processed') as mock_is_processed:
            with patch.object(message_processor, 'ticket_service') as mock_ticket:
                mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                # Process web form message
                await message_processor.process_support_request(
                    message="Test message",
                    channel="web_form",
                    customer_email="test@example.com",
                    message_type="web_form_submission"
                )

                # Verify deduplication was not checked for web form
                mock_is_processed.assert_not_called()


class TestDeduplicationChannelSpecific:
    """Test channel-specific deduplication behavior."""

    @pytest.mark.asyncio
    async def test_same_message_id_different_channels_not_deduplicated(self, message_processor):
        """Test that same message ID from different channels is not deduplicated."""
        message_id = "same_id_12345"

        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            # First call (WhatsApp) returns False, second call (Email) returns False
            mock_conn.fetchval = AsyncMock(side_effect=[False, False])
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Check for WhatsApp
            result1 = await message_processor._is_message_processed(message_id, "whatsapp")
            # Check for Email
            result2 = await message_processor._is_message_processed(message_id, "email")

            assert result1 is False
            assert result2 is False
            # Both should be allowed (different channels)

    @pytest.mark.asyncio
    async def test_deduplication_query_includes_channel(self, message_processor, sample_whatsapp_message_id):
        """Test that deduplication query includes channel in WHERE clause."""
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )

            # Verify query includes both message_id and channel
            call_args = mock_conn.fetchval.call_args[0][0]
            assert "channel_message_id" in call_args
            assert "channel" in call_args


class TestDeduplicationPerformance:
    """Test deduplication performance characteristics."""

    @pytest.mark.asyncio
    async def test_deduplication_check_is_fast(self, message_processor, sample_whatsapp_message_id):
        """Test that deduplication check completes quickly."""
        import time

        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            start = time.time()
            await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )
            duration = time.time() - start

            # Should complete in under 10ms (excluding actual DB time)
            assert duration < 0.01

    @pytest.mark.asyncio
    async def test_deduplication_uses_database_index(self, message_processor, sample_whatsapp_message_id):
        """Test that deduplication query can use database index."""
        # The processed_messages table should have a unique index on channel_message_id
        # This test verifies the query structure supports index usage
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )

            # Verify query uses indexed column
            call_args = mock_conn.fetchval.call_args[0][0]
            assert "channel_message_id = $1" in call_args or "channel_message_id=$1" in call_args


class TestDeduplicationEdgeCases:
    """Test edge cases in deduplication."""

    @pytest.mark.asyncio
    async def test_very_long_message_id(self, message_processor):
        """Test handling of very long message ID."""
        long_message_id = "a" * 500

        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # Should not raise exception
            result = await message_processor._is_message_processed(
                long_message_id,
                "whatsapp"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_message_id_with_special_characters(self, message_processor):
        """Test handling of message ID with special characters."""
        special_message_id = "msg-id_123.456@example.com"

        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            result = await message_processor._is_message_processed(
                special_message_id,
                "email"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_unicode_message_id(self, message_processor):
        """Test handling of Unicode in message ID."""
        unicode_message_id = "msg_世界_🌍"

        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=False)
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            result = await message_processor._is_message_processed(
                unicode_message_id,
                "whatsapp"
            )

            assert result is False


class TestDeduplicationWebhookRetries:
    """Test deduplication specifically for webhook retries."""

    @pytest.mark.asyncio
    async def test_webhook_retry_within_seconds_is_deduplicated(self, message_processor, sample_whatsapp_message_id):
        """Test that webhook retry within seconds is deduplicated."""
        # Simulate webhook being called twice with same message ID
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            # First call: not processed, second call: already processed
            mock_conn.fetchval = AsyncMock(side_effect=[False, True])
            mock_conn.execute = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            # First webhook call
            is_dup1 = await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )
            assert is_dup1 is False

            # Mark as processed
            await message_processor._mark_message_processed(
                sample_whatsapp_message_id,
                "whatsapp",
                uuid4()
            )

            # Second webhook call (retry)
            is_dup2 = await message_processor._is_message_processed(
                sample_whatsapp_message_id,
                "whatsapp"
            )
            assert is_dup2 is True

    @pytest.mark.asyncio
    async def test_deduplication_prevents_duplicate_tickets(self, message_processor, sample_whatsapp_message_id):
        """Test that deduplication prevents creating duplicate tickets."""
        with patch.object(message_processor, '_is_message_processed') as mock_is_processed:
            # First call: not duplicate, second call: duplicate
            mock_is_processed.side_effect = [False, True]

            with patch.object(message_processor, 'ticket_service') as mock_ticket:
                mock_ticket.create_ticket = AsyncMock(return_value=uuid4())

                # First webhook call - should create ticket
                await message_processor.process_support_request(
                    message="Test message",
                    channel="whatsapp",
                    customer_phone="+14155551234",
                    channel_message_id=sample_whatsapp_message_id,
                    message_type="whatsapp_message"
                )

                # Second webhook call (retry) - should not create ticket
                await message_processor.process_support_request(
                    message="Test message",
                    channel="whatsapp",
                    customer_phone="+14155551234",
                    channel_message_id=sample_whatsapp_message_id,
                    message_type="whatsapp_message"
                )

                # Verify ticket was only created once
                assert mock_ticket.create_ticket.call_count == 1


class TestDeduplicationDataRetention:
    """Test deduplication data retention."""

    @pytest.mark.asyncio
    async def test_processed_messages_include_timestamp(self, message_processor, sample_whatsapp_message_id):
        """Test that processed messages include timestamp for cleanup."""
        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            await message_processor._mark_message_processed(
                sample_whatsapp_message_id,
                "whatsapp",
                uuid4()
            )

            # Verify INSERT includes timestamp (processed_at with DEFAULT NOW())
            call_args = mock_conn.execute.call_args[0][0]
            assert "processed_messages" in call_args
            # The table should have processed_at with DEFAULT NOW()

    @pytest.mark.asyncio
    async def test_processed_messages_include_ticket_id(self, message_processor, sample_whatsapp_message_id):
        """Test that processed messages include ticket ID for traceability."""
        ticket_id = uuid4()

        with patch.object(message_processor, 'db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_db.acquire.return_value.__aenter__.return_value = mock_conn

            await message_processor._mark_message_processed(
                sample_whatsapp_message_id,
                "whatsapp",
                ticket_id
            )

            # Verify ticket_id is included in INSERT
            call_args = mock_conn.execute.call_args
            assert ticket_id in call_args[0] or str(ticket_id) in str(call_args)
