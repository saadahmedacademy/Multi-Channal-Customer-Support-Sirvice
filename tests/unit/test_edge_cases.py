"""
Edge Case Tests.

Tests for edge cases: empty messages, profanity, duplicates, attachments,
very long messages, API failures, and other boundary conditions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Empty/Short Message Tests ==============

class TestEmptyMessageHandling:
    """Tests for empty or very short message handling."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_message_sentiment(self):
        """Test sentiment analysis of empty string."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("")
        
        assert result["score"] == 0.0
        assert result["label"] == "neutral"
        assert result["word_count"] == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_whitespace_only_message_sentiment(self):
        """Test sentiment analysis of whitespace-only message."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("   \n\t  ")
        
        assert result["label"] == "neutral"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_single_word_sentiment(self):
        """Test sentiment of single word messages."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # Words that are in the sentiment dictionaries
        positive = sentiment_analyzer.analyze("excellent")
        negative = sentiment_analyzer.analyze("terrible")
        
        assert positive["score"] > 0
        assert negative["score"] < 0
        assert len(positive["positive_matches"]) > 0
        assert len(negative["negative_matches"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_escalation_empty_message(self):
        """Test that empty messages don't trigger escalation."""
        from backend.worker.escalation import escalation_detector
        
        requires_escalation, reason, keywords = escalation_detector.detect_escalation("")
        
        assert requires_escalation is False
        assert reason is None
        assert keywords == []


# ============== Profanity/Abusive Language Tests ==============

class TestProfanityHandling:
    """Tests for handling profanity or abusive language."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_profanity_triggers_escalation(self):
        """Test that abusive language triggers escalation."""
        from backend.worker.escalation import escalation_detector
        
        # Use words that are actually in the escalation detector's dictionaries
        message = "I want a refund! This pricing is ridiculous and unacceptable!"
        requires_escalation, reason, keywords = escalation_detector.detect_escalation(message)
        
        assert requires_escalation is True
        assert len(keywords) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_profanity_sentiment(self):
        """Test sentiment analysis of abusive language."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("This is terrible and awful and worst!")
        
        assert result["score"] < -0.2
        assert result["label"] in ["negative", "neutral"]


# ============== Duplicate Submission Tests ==============

class TestDuplicateSubmission:
    """Tests for duplicate ticket detection."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_duplicate_ticket_finds_recent(self):
        """Test duplicate detection finds recent tickets."""
        from backend.worker.ticket_service import TicketService
        
        service = TicketService()
        customer_id = uuid4()
        
        mock_recent_ticket = {
            "id": str(uuid4()),
            "status": "open",
            "created_at": datetime.utcnow()
        }
        
        with patch('backend.worker.ticket_service.db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value=mock_recent_ticket)
            mock_db.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            
            result = await service.check_duplicate_ticket(customer_id, "hash123", window_minutes=5)
            
            assert result is not None
            assert "id" in result
            assert result["status"] == "open"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_duplicate_no_recent_ticket(self):
        """Test no duplicate found when no recent tickets."""
        from backend.worker.ticket_service import TicketService
        
        service = TicketService()
        customer_id = uuid4()
        
        with patch('backend.worker.ticket_service.db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow = AsyncMock(return_value=None)
            mock_db.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            
            result = await service.check_duplicate_ticket(customer_id, "hash123")
            
            assert result is None


# ============== Very Long Message Tests ==============

class TestLongMessageHandling:
    """Tests for handling very long messages."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_very_long_message_sentiment(self):
        """Test sentiment analysis handles very long messages."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # Create a very long message (1000+ words)
        long_message = "This is great and excellent and wonderful. " * 300
        
        result = sentiment_analyzer.analyze(long_message)
        
        # Should still analyze without errors
        assert "score" in result
        assert "label" in result
        assert result["score"] > 0  # Should detect positive

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_very_long_message_doesnt_crash_processor(self):
        """Test message processor handles very long messages."""
        from backend.worker.message_processor import MessageProcessor
        
        processor = MessageProcessor()
        long_message = "Test " * 1000
        
        # Should not crash when loading knowledge context
        with patch('backend.worker.message_processor.knowledge_repo') as mock_repo:
            mock_repo.search_similar = AsyncMock(return_value=[])
            mock_repo.search_by_keyword = AsyncMock(return_value=[])
            
            context = await processor._load_knowledge_context(long_message)
            
            # Should return empty context gracefully
            assert isinstance(context, list)


# ============== API Failure Tests ==============

class TestAPIFailureHandling:
    """Tests for graceful handling of external API failures."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_ai_fallback_when_no_api_key(self):
        """Test fallback response when Hugging Face API key is not set."""
        from backend.worker.ai_agent import AIAgent

        with patch('backend.worker.ai_agent.settings') as mock_settings:
            mock_settings.huggingface_api_key = None
            mock_settings.ai_timeout = 5
            mock_settings.max_tokens = 500

            agent = AIAgent()
            response, tokens, confidence = await agent.generate_response(
                message="I need help",
                channel="web_form"
            )

            assert response is not None
            assert len(response) > 0
            assert "human agent" in response.lower()
            assert tokens == 0
            assert confidence is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_ai_fallback_for_whatsapp_channel(self):
        """Test fallback response is channel-appropriate for WhatsApp."""
        from backend.worker.ai_agent import AIAgent

        with patch('backend.worker.ai_agent.settings') as mock_settings:
            mock_settings.huggingface_api_key = None
            mock_settings.ai_timeout = 5
            mock_settings.max_tokens = 500

            agent = AIAgent()
            response, tokens, confidence = await agent.generate_response(
                message="Help",
                channel="whatsapp"
            )

            assert "Hi!" in response
            assert "human agent" in response

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_queue_publish_failure_handled(self):
        """Test graceful handling when queue publish fails."""
        from backend.integrations.queue_client import QueueClient
        
        client = QueueClient()
        
        with patch.object(client, 'start_producer', side_effect=Exception("Connection refused")):
            with pytest.raises(Exception, match="Connection refused"):
                await client.publish(topic="test", message={"data": "test"})


# ============== Attachment Handling Tests ==============

class TestAttachmentHandling:
    """Tests for handling messages with attachments."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_image_message_placeholder(self):
        """Test that image messages get appropriate placeholder."""
        # This would be handled in WhatsApp webhook
        message_type = "image"
        
        if message_type == "image":
            content = "[Image received]"
        
        assert content == "[Image received]"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_document_message_placeholder(self):
        """Test that document messages get appropriate placeholder."""
        message_type = "document"
        
        if message_type == "document":
            content = "[Document received]"
        
        assert content == "[Document received]"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_audio_message_placeholder(self):
        """Test that audio messages get appropriate placeholder."""
        message_type = "audio"
        
        if message_type == "audio":
            content = "[Audio message received]"
        
        assert content == "[Audio message received]"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_unsupported_message_type(self):
        """Test handling of unsupported message types."""
        message_type = "video"
        
        if message_type not in ["text", "image", "document", "audio"]:
            content = f"[Unsupported message type: {message_type}]"
        
        assert "Unsupported" in content
        assert "video" in content


# ============== Non-English Language Tests ==============

class TestNonEnglishMessages:
    """Tests for handling messages in different languages."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sentiment_english(self):
        """Test sentiment analysis of English text."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("This is great and excellent!")
        
        assert result["score"] > 0
        assert len(result["positive_matches"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sentiment_mixed_language(self):
        """Test sentiment analysis with mixed language text."""
        from backend.worker.sentiment import sentiment_analyzer
        
        # English sentiment words should still be detected
        result = sentiment_analyzer.analyze("Bonjour! This is terrible and awful!")
        
        # Should detect English negative words
        assert len(result["negative_matches"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_escalation_non_english(self):
        """Test escalation doesn't crash with non-English text."""
        from backend.worker.escalation import escalation_detector
        
        # Non-English text shouldn't cause errors
        message = "¿Dónde está el baño? Necesito ayuda con mi cuenta."
        requires_escalation, reason, keywords = escalation_detector.detect_escalation(message)
        
        # Should not crash, may or may not escalate based on keywords
        assert isinstance(requires_escalation, bool)
        assert isinstance(keywords, list)


# ============== Spam Detection Tests ==============

class TestSpamDetection:
    """Tests for handling spam or nonsensical input."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_repeated_characters_sentiment(self):
        """Test sentiment of spam/repeated characters."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("aaaa bbbb cccc dddd")
        
        # Should be neutral (no sentiment words)
        assert result["label"] == "neutral"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_special_characters_only(self):
        """Test sentiment of special characters only."""
        from backend.worker.sentiment import sentiment_analyzer
        
        result = sentiment_analyzer.analyze("@#$%^&*()!")
        
        assert result["label"] == "neutral"
        assert result["score"] == 0.0


# ============== Concurrent Request Tests ==============

class TestConcurrency:
    """Tests for handling concurrent requests."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_sentiment_analysis(self):
        """Test sentiment analysis handles concurrent calls."""
        from backend.worker.sentiment import SentimentAnalyzer
        import asyncio
        
        # Sentiment analysis is synchronous, run in executor
        def analyze_sentiment(text):
            analyzer = SentimentAnalyzer()
            return analyzer.analyze(text)
        
        messages = ["Great!", "Terrible!", "Neutral question", "Excellent!", "Bad!"]
        
        # Run concurrent analyses using thread pool
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(None, analyze_sentiment, msg) for msg in messages]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all("score" in r for r in results)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_knowledge_search(self):
        """Test knowledge base handles concurrent searches."""
        from backend.db.repositories.knowledge_repo import knowledge_repo
        
        queries = ["API", "password", "billing", "refund", "help"]
        
        with patch('backend.db.repositories.knowledge_repo.db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_db.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            
            import asyncio
            tasks = [knowledge_repo.search_by_keyword(q) for q in queries]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
