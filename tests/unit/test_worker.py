"""
Unit tests for worker services.

Tests for AI agent, escalation detector, sentiment analyzer, and ticket service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.worker.ai_agent import AIAgent, CHANNEL_CONFIGS
from backend.worker.escalation import EscalationDetector, DEFAULT_ESCALATION_KEYWORDS
from backend.worker.sentiment import SentimentAnalyzer, analyze_sentiment
from backend.worker.ticket_service import TicketService


# ============== AI Agent Tests ==============

class TestAIAgent:
    """Tests for AI agent response generation."""

    @pytest.fixture
    def ai_agent(self):
        """Create AI agent instance for testing."""
        with patch('backend.worker.ai_agent.settings') as mock_settings:
            mock_settings.huggingface_api_key = None
            mock_settings.ai_timeout = 30
            mock_settings.max_tokens = 500
            agent = AIAgent()
            return agent

    @pytest.mark.unit
    def test_channel_configs_exist(self):
        """Test that channel configurations are defined."""
        assert "web_form" in CHANNEL_CONFIGS
        assert "whatsapp" in CHANNEL_CONFIGS
        assert "email" in CHANNEL_CONFIGS

    @pytest.mark.unit
    def test_web_form_channel_config(self):
        """Test web form channel configuration."""
        config = CHANNEL_CONFIGS["web_form"]
        assert config["tone"] == "professional and helpful"
        assert config["max_length"] == 1000
        assert "detailed" in config["format"]

    @pytest.mark.unit
    def test_whatsapp_channel_config(self):
        """Test WhatsApp channel configuration."""
        config = CHANNEL_CONFIGS["whatsapp"]
        assert config["tone"] == "friendly and conversational"
        assert config["max_length"] == 300
        assert "concise" in config["format"]

    @pytest.mark.unit
    def test_get_system_prompt(self, ai_agent):
        """Test system prompt generation."""
        prompt = ai_agent._get_system_prompt("web_form")
        
        assert "friendly customer support assistant" in prompt
        assert "professional and helpful" in prompt
        assert "Thank you for contacting our AI Support Center" in prompt

    @pytest.mark.unit
    def test_get_system_prompt_with_knowledge(self, ai_agent):
        """Test system prompt with knowledge base context."""
        knowledge = [
            {"title": "API Keys", "content": "API keys can be generated from dashboard"}
        ]
        prompt = ai_agent._get_system_prompt("web_form", knowledge)
        
        assert "Relevant Knowledge Base" in prompt
        assert "API Keys" in prompt

    @pytest.mark.unit
    def test_fallback_response(self, ai_agent):
        """Test fallback response when AI is unavailable."""
        response = ai_agent._get_fallback_response("web_form")
        
        assert "Thank you for your message" in response
        assert "human agent" in response

    @pytest.mark.unit
    def test_fallback_response_whatsapp(self, ai_agent):
        """Test fallback response for WhatsApp channel."""
        response = ai_agent._get_fallback_response("whatsapp")
        
        assert "Hi!" in response  # WhatsApp greeting
        assert "human agent" in response

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_generate_response_no_api_keys(self, ai_agent):
        """Test response generation when no API keys configured."""
        response, tokens, confidence = await ai_agent.generate_response(
            message="Test message",
            channel="web_form"
        )
        
        assert response is not None
        assert tokens == 0
        assert confidence is None
        assert "human agent" in response


# ============== Escalation Detector Tests ==============

class TestEscalationDetector:
    """Tests for escalation detection logic."""

    @pytest.fixture
    def detector(self):
        """Create escalation detector for testing."""
        return EscalationDetector(escalation_rules_path=None)

    @pytest.mark.unit
    def test_detect_pricing_keywords(self, detector):
        """Test detection of pricing-related keywords."""
        message = "How much does the pro plan cost?"
        requires_escalation, reason, keywords = detector.detect_escalation(message)
        
        assert requires_escalation is True
        assert "Pricing" in reason
        assert any(kw in keywords for kw in ["cost", "plan"])

    @pytest.mark.unit
    def test_detect_refund_keywords(self, detector):
        """Test detection of refund request."""
        message = "I want a refund for my last payment"
        requires_escalation, reason, keywords = detector.detect_escalation(message)
        
        assert requires_escalation is True
        assert "Refund" in reason
        assert "refund" in keywords

    @pytest.mark.unit
    def test_detect_legal_keywords(self, detector):
        """Test detection of legal topics."""
        message = "I'm going to contact my lawyer about this"
        requires_escalation, reason, keywords = detector.detect_escalation(message)
        
        assert requires_escalation is True
        assert "Legal" in reason
        assert "lawyer" in keywords

    @pytest.mark.unit
    def test_detect_human_request(self, detector):
        """Test detection of human agent request."""
        message = "I want to speak to a real person"
        requires_escalation, reason, keywords = detector.detect_escalation(message)
        
        assert requires_escalation is True
        assert "human" in reason.lower()
        assert any(kw in keywords for kw in ["human", "person"])

    @pytest.mark.unit
    def test_detect_angry_sentiment(self, detector):
        """Test detection of angry customer sentiment."""
        message = "This is absolutely terrible and unacceptable!"
        requires_escalation, reason, keywords = detector.detect_escalation(
            message, sentiment_score=-0.8
        )
        
        assert requires_escalation is True
        assert "sentiment" in reason.lower() or "Negative" in reason

    @pytest.mark.unit
    def test_no_escalation_normal_message(self, detector):
        """Test that normal messages don't trigger escalation."""
        message = "How do I reset my password?"
        requires_escalation, reason, keywords = detector.detect_escalation(message)
        
        assert requires_escalation is False
        assert reason is None
        assert keywords == []

    @pytest.mark.unit
    def test_sentiment_threshold(self, detector):
        """Test sentiment threshold for escalation."""
        detector.sentiment_threshold = 0.3
        
        # Score below threshold should escalate
        requires, _, _ = detector.detect_escalation("test", sentiment_score=-0.5)
        assert requires is True
        
        # Score above threshold should not escalate
        requires, _, _ = detector.detect_escalation("test", sentiment_score=0.5)
        assert requires is False

    @pytest.mark.unit
    def test_get_escalation_email_legal(self, detector):
        """Test escalation email routing for legal issues."""
        email = detector.get_escalation_email("legal", "high")
        assert email == "legal@company.com"

    @pytest.mark.unit
    def test_get_escalation_email_billing(self, detector):
        """Test escalation email routing for billing issues."""
        email = detector.get_escalation_email("refund", "medium")
        assert email == "billing@company.com"


# ============== Sentiment Analyzer Tests ==============

class TestSentimentAnalyzer:
    """Tests for sentiment analysis."""

    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer for testing."""
        return SentimentAnalyzer()

    @pytest.mark.unit
    def test_positive_sentiment(self, analyzer):
        """Test detection of positive sentiment."""
        result = analyzer.analyze("This is great excellent amazing wonderful!")
        
        assert result["score"] > 0.1, f"Expected positive score, got {result['score']}"
        assert len(result["positive_matches"]) > 0, "Should have positive matches"

    @pytest.mark.unit
    def test_negative_sentiment(self, analyzer):
        """Test detection of negative sentiment."""
        result = analyzer.analyze("This is terrible awful horrible worst!")
        
        assert result["score"] < -0.1, f"Expected negative score, got {result['score']}"
        assert len(result["negative_matches"]) > 0, "Should have negative matches"

    @pytest.mark.unit
    def test_neutral_sentiment(self, analyzer):
        """Test detection of neutral sentiment."""
        result = analyzer.analyze("I have a question about my account")
        
        assert result["label"] == "neutral"
        assert abs(result["score"]) <= 0.3

    @pytest.mark.unit
    def test_intensifiers(self, analyzer):
        """Test that intensifiers increase sentiment score."""
        normal = analyzer.analyze("This is good")
        intensified = analyzer.analyze("This is very good")
        
        assert intensified["score"] > normal["score"]

    @pytest.mark.unit
    def test_negation(self, analyzer):
        """Test that negation reduces sentiment score."""
        positive = analyzer.analyze("This is working")
        negated = analyzer.analyze("This is not working")
        
        assert negated["score"] < positive["score"]

    @pytest.mark.unit
    def test_requires_escalation_negative(self, analyzer):
        """Test escalation requirement for negative sentiment."""
        assert analyzer.requires_escalation(-0.5) is True
        assert analyzer.requires_escalation(-0.8) is True

    @pytest.mark.unit
    def test_requires_escalation_positive(self, analyzer):
        """Test no escalation for positive sentiment."""
        assert analyzer.requires_escalation(0.5) is False
        assert analyzer.requires_escalation(0.8) is False

    @pytest.mark.unit
    def test_convenience_function(self):
        """Test the convenience analyze_sentiment function."""
        result = analyze_sentiment("Thank you so much!")
        assert result["score"] > 0


# ============== Ticket Service Tests ==============

class TestTicketService:
    """Tests for ticket service operations."""

    @pytest.fixture
    def ticket_service(self):
        """Create ticket service for testing."""
        return TicketService()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_ticket(self, ticket_service, sample_customer_data, 
                                  sample_conversation_data, mock_db_pool):
        """Test ticket creation."""
        with patch('backend.worker.ticket_service.ticket_repo') as mock_repo:
            mock_ticket = MagicMock()
            mock_ticket.id = sample_conversation_data["id"]
            mock_ticket.to_dict.return_value = {"id": str(sample_conversation_data["id"])}
            mock_repo.create = AsyncMock(return_value=mock_ticket)
            
            ticket = await ticket_service.create_ticket(
                conversation_id=sample_conversation_data["id"],
                customer_id=sample_customer_data["id"],
                source_channel="web_form",
                category="technical"
            )
            
            assert ticket is not None
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_update_ticket_status(self, ticket_service, mock_db_pool):
        """Test ticket status update."""
        with patch('backend.worker.ticket_service.ticket_repo') as mock_repo:
            mock_ticket = MagicMock()
            mock_ticket.to_dict.return_value = {"status": "resolved"}
            mock_repo.update_status = AsyncMock(return_value=mock_ticket)
            
            result = await ticket_service.update_ticket_status(
                ticket_id=uuid4(),
                status="resolved"
            )
            
            assert result is not None
            mock_repo.update_status.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_escalate_ticket(self, ticket_service, mock_db_pool):
        """Test ticket escalation."""
        with patch('backend.worker.ticket_service.ticket_repo') as mock_repo:
            mock_repo.update_status = AsyncMock(return_value=MagicMock())
            
            result = await ticket_service.escalate_ticket(
                ticket_id=uuid4(),
                reason="Customer requested human agent"
            )
            
            assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_add_message(self, ticket_service, mock_db_pool):
        """Test adding message to conversation."""
        with patch('backend.worker.ticket_service.db') as mock_db:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock()
            mock_db.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            
            result = await ticket_service.add_message(
                conversation_id=uuid4(),
                channel="web_form",
                direction="outbound",
                role="agent",
                content="Test response"
            )
            
            assert result is True
            mock_conn.execute.assert_called_once()


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
