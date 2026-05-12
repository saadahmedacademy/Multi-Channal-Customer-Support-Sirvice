"""
Conversation History Retrieval Tests.

Tests for conversation history loading in message processor and repository.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Fixtures ==============

@pytest.fixture
def mock_db_conn():
    """Mock database connection."""
    with patch('backend.db.repositories.conversation_repo.db') as mock_db:
        mock_conn = AsyncMock()
        mock_db.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_db, mock_conn


@pytest.fixture
def conversation_repo():
    """Create conversation repository instance."""
    from backend.db.repositories.conversation_repo import ConversationRepository
    return ConversationRepository()


# ============== Get Messages Tests ==============

class TestConversationGetMessages:
    """Tests for retrieving messages from a conversation."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_messages_returns_chronological_order(self, conversation_repo, mock_db_conn):
        """Test that messages are returned in chronological order (oldest first)."""
        mock_db, mock_conn = mock_db_conn
        
        # Mock DB returns messages in DESC order (newest first)
        mock_rows = [
            {"role": "agent", "content": "Response 3"},
            {"role": "customer", "content": "Question 2"},
            {"role": "customer", "content": "Question 1"}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        conversation_id = uuid4()
        messages = await conversation_repo.get_messages(conversation_id, limit=10)

        # Should be reversed to chronological order
        assert len(messages) == 3
        assert messages[0]["content"] == "Question 1"
        assert messages[1]["content"] == "Question 2"
        assert messages[2]["content"] == "Response 3"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_messages_respects_limit(self, conversation_repo, mock_db_conn):
        """Test that limit parameter is respected."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        conversation_id = uuid4()
        await conversation_repo.get_messages(conversation_id, limit=5)

        query = mock_conn.fetch.call_args[0][0]
        assert "$2" in query  # Second param placeholder

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_messages_empty_conversation(self, conversation_repo, mock_db_conn):
        """Test getting messages from empty conversation."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        conversation_id = uuid4()
        messages = await conversation_repo.get_messages(conversation_id)

        assert len(messages) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_messages_includes_all_fields(self, conversation_repo, mock_db_conn):
        """Test that message objects include role and content."""
        mock_db, mock_conn = mock_db_conn
        
        mock_rows = [
            {"role": "customer", "content": "Hello, I need help"},
            {"role": "agent", "content": "Sure, how can I assist?"}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        messages = await conversation_repo.get_messages(uuid4())

        for msg in messages:
            assert "role" in msg
            assert "content" in msg
            assert isinstance(msg["role"], str)
            assert isinstance(msg["content"], str)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_messages_with_different_roles(self, conversation_repo, mock_db_conn):
        """Test messages with different roles are handled correctly."""
        mock_db, mock_conn = mock_db_conn
        
        mock_rows = [
            {"role": "system", "content": "System notification"},
            {"role": "agent", "content": "Agent response"},
            {"role": "customer", "content": "Customer question"}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        messages = await conversation_repo.get_messages(uuid4())

        roles = [msg["role"] for msg in messages]
        assert "customer" in roles
        assert "agent" in roles
        assert "system" in roles

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_messages_handles_database_error(self, conversation_repo, mock_db_conn):
        """Test graceful handling of database errors."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(side_effect=Exception("Database connection lost"))

        # The repository doesn't catch errors, so they should propagate
        with pytest.raises(Exception, match="Database connection lost"):
            await conversation_repo.get_messages(uuid4())


# ============== Message Processor Conversation History Tests ==============

class TestMessageProcessorConversationHistory:
    """Tests for message processor's conversation history retrieval."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_conversation_history_uses_repo(self):
        """Test that message processor uses conversation_repo.get_messages."""
        from backend.worker.message_processor import MessageProcessor
        from backend.db.repositories.conversation_repo import conversation_repo
        
        processor = MessageProcessor()
        conversation_id = str(uuid4())
        
        mock_messages = [
            {"role": "customer", "content": "Question"},
            {"role": "agent", "content": "Answer"}
        ]
        
        with patch.object(conversation_repo, 'get_messages', return_value=mock_messages) as mock_get:
            history = await processor._get_conversation_history(conversation_id, limit=5)
            
            mock_get.assert_called_once()
            assert len(history) == 2
            assert history[0]["content"] == "Question"
            assert history[1]["content"] == "Answer"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_conversation_history_handles_error(self):
        """Test graceful error handling in conversation history retrieval."""
        from backend.worker.message_processor import MessageProcessor
        from backend.db.repositories.conversation_repo import conversation_repo
        
        processor = MessageProcessor()
        
        with patch.object(conversation_repo, 'get_messages', side_effect=Exception("DB error")):
            history = await processor._get_conversation_history(str(uuid4()))
            
            # Should return empty list on error
            assert history == []

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_conversation_history_default_limit(self):
        """Test that default limit is 10 messages."""
        from backend.worker.message_processor import MessageProcessor
        from backend.db.repositories.conversation_repo import conversation_repo
        
        processor = MessageProcessor()
        
        with patch.object(conversation_repo, 'get_messages', return_value=[]) as mock_get:
            await processor._get_conversation_history(str(uuid4()))
            
            # Should use default limit of 10
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs['limit'] == 10


# ============== Cross-Channel Conversation Tests ==============

class TestCrossChannelConversationHistory:
    """Tests for cross-channel conversation continuity."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_active_conversation_24h_window(self, mock_db_conn):
        """Test retrieving active conversation within 24 hours."""
        from backend.db.repositories.conversation_repo import ConversationRepository
        
        repo = ConversationRepository()
        mock_db, mock_conn = mock_db_conn
        
        mock_row = {
            "id": uuid4(),
            "customer_id": uuid4(),
            "initial_channel": "web_form",
            "started_at": datetime.utcnow() - timedelta(hours=2),
            "ended_at": None,
            "status": "active",
            "sentiment_score": None,
            "resolution_type": None,
            "escalated_to": None,
            "metadata": "{}"
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        customer_id = uuid4()
        conversation = await repo.get_active_by_customer(customer_id, hours=24)

        assert conversation is not None
        assert conversation.status == "active"
        assert conversation.initial_channel == "web_form"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_no_active_conversation_outside_window(self, mock_db_conn):
        """Test no conversation returned outside time window."""
        from backend.db.repositories.conversation_repo import ConversationRepository
        
        repo = ConversationRepository()
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetchrow = AsyncMock(return_value=None)

        customer_id = uuid4()
        conversation = await repo.get_active_by_customer(customer_id, hours=1)

        assert conversation is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cross_channel_message_history(self, conversation_repo, mock_db_conn):
        """Test that message history includes messages from all channels."""
        mock_db, mock_conn = mock_db_conn
        
        # Simulate multi-channel conversation (DB returns DESC, repo reverses to ASC)
        mock_rows = [
            {"role": "agent", "content": "Response via WhatsApp"},
            {"role": "customer", "content": "Follow-up via WhatsApp"},
            {"role": "agent", "content": "Response via web"},
            {"role": "customer", "content": "Submitted via web form"}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_rows)

        messages = await conversation_repo.get_messages(uuid4(), limit=10)

        assert len(messages) == 4
        # Should be in chronological order (oldest first after reversal)
        assert "web form" in messages[0]["content"]
        assert "WhatsApp" in messages[2]["content"]


# ============== Conversation Status Tests ==============

class TestConversationStatus:
    """Tests for conversation status management."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_status_to_escalated(self, mock_db_conn):
        """Test updating conversation status to escalated."""
        from backend.db.repositories.conversation_repo import ConversationRepository
        
        repo = ConversationRepository()
        mock_db, mock_conn = mock_db_conn
        
        mock_row = {
            "id": uuid4(),
            "customer_id": uuid4(),
            "initial_channel": "whatsapp",
            "started_at": datetime.utcnow(),
            "ended_at": None,
            "status": "escalated",
            "sentiment_score": None,
            "resolution_type": None,
            "escalated_to": None,
            "metadata": "{}"
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        conversation_id = uuid4()
        result = await repo.update_status(conversation_id, "escalated")

        assert result is not None
        assert result.status == "escalated"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_status_to_closed(self, mock_db_conn):
        """Test updating conversation status to closed."""
        from backend.db.repositories.conversation_repo import ConversationRepository
        
        repo = ConversationRepository()
        mock_db, mock_conn = mock_db_conn
        
        mock_row = {
            "id": uuid4(),
            "customer_id": uuid4(),
            "initial_channel": "web_form",
            "started_at": datetime.utcnow(),
            "ended_at": datetime.utcnow(),
            "status": "closed",
            "sentiment_score": None,
            "resolution_type": None,
            "escalated_to": None,
            "metadata": "{}"
        }
        mock_conn.fetchrow = AsyncMock(return_value=mock_row)

        conversation_id = uuid4()
        ended_at = datetime.utcnow()
        result = await repo.update_status(conversation_id, "closed", ended_at=ended_at)

        assert result is not None
        assert result.status == "closed"


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
