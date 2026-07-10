"""Unit tests for AI agent functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.worker.ai_agent import AIAgent


@pytest.fixture
def ai_agent():
    """Create AI agent instance for testing."""
    return AIAgent()


class TestAIAgentInitialization:
    """Test AI agent initialization."""

    def test_ai_agent_initializes_successfully(self, ai_agent):
        """Test that AI agent initializes without errors."""
        assert ai_agent is not None
        assert hasattr(ai_agent, 'generate_response')

    def test_ai_agent_has_required_methods(self, ai_agent):
        """Test that AI agent has all required methods."""
        assert hasattr(ai_agent, 'generate_response')
        assert hasattr(ai_agent, '_get_system_prompt')
        assert hasattr(ai_agent, '_get_fallback_response')


class TestResponseGeneration:
    """Test AI response generation."""

    @pytest.mark.asyncio
    async def test_generate_response_basic(self, ai_agent):
        """Test basic response generation."""
        with patch.object(ai_agent, '_call_huggingface', new=AsyncMock(return_value=("Thank you for contacting support. I can help you with that.", 10))), \
             patch.object(ai_agent, 'huggingface_api_key', "test-key"):
            response, tokens, confidence = await ai_agent.generate_response(
                message="I need help with my account",
                channel="web_form",
                conversation_history=[]
            )
            assert response is not None
            assert len(response) > 0
            assert tokens > 0

    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(self, ai_agent):
        """Test response generation with conversation history."""
        conversation_history = [
            {"role": "user", "content": "I need help"},
            {"role": "assistant", "content": "How can I assist you?"},
            {"role": "user", "content": "My account is locked"},
        ]

        with patch.object(ai_agent, '_call_huggingface', new=AsyncMock(return_value=("I'll help you unlock your account.", 10))), \
             patch.object(ai_agent, 'huggingface_api_key', "test-key"):
            response, tokens, confidence = await ai_agent.generate_response(
                message="Can you help me?",
                channel="web_form",
                conversation_history=conversation_history
            )
            assert response is not None

    @pytest.mark.asyncio
    async def test_generate_response_handles_api_errors(self, ai_agent):
        """Test that API errors are handled gracefully."""
        with patch.object(ai_agent, '_call_huggingface', new=AsyncMock(return_value=(None, 0))), \
             patch.object(ai_agent, 'huggingface_api_key', "test-key"):
            response, tokens, confidence = await ai_agent.generate_response(
                message="Test message",
                channel="web_form",
                conversation_history=[]
            )
            assert response is not None
            assert "unavailable" in response.lower()


class TestFallbackResponse:
    """Test fallback response generation."""

    def test_fallback_response_for_web_form(self, ai_agent):
        """Test fallback response for web form channel."""
        response = ai_agent._get_fallback_response("web_form")
        assert response is not None
        assert "Thank you" in response
        assert len(response) <= 1000

    def test_fallback_response_for_whatsapp(self, ai_agent):
        """Test fallback response for WhatsApp channel."""
        response = ai_agent._get_fallback_response("whatsapp")
        assert response is not None
        assert len(response) <= 300

    def test_fallback_response_for_email(self, ai_agent):
        """Test fallback response for email channel."""
        response = ai_agent._get_fallback_response("email")
        assert response is not None
        assert "Dear" in response or "Valued" in response
        assert len(response) <= 800


class TestErrorHandling:
    """Test error handling in AI agent."""

    @pytest.mark.asyncio
    async def test_handles_empty_message(self, ai_agent):
        """Test handling of empty message."""
        with patch.object(ai_agent, '_call_huggingface', new=AsyncMock(return_value=("How can I help you today?", 5))), \
             patch.object(ai_agent, 'huggingface_api_key', "test-key"):
            response, tokens, confidence = await ai_agent.generate_response(
                message="",
                channel="web_form",
                conversation_history=[]
            )
            assert response is not None

    @pytest.mark.asyncio
    async def test_handles_very_long_message(self, ai_agent):
        """Test handling of very long message."""
        long_message = "test " * 1000

        with patch.object(ai_agent, '_call_huggingface', new=AsyncMock(return_value=("I understand your concern.", 5))), \
             patch.object(ai_agent, 'huggingface_api_key', "test-key"):
            response, tokens, confidence = await ai_agent.generate_response(
                message=long_message,
                channel="web_form",
                conversation_history=[]
            )
            assert response is not None


class TestPerformance:
    """Test AI agent performance characteristics."""

    @pytest.mark.asyncio
    async def test_handles_concurrent_requests(self, ai_agent):
        """Test that AI agent can handle concurrent requests."""
        import asyncio

        with patch.object(ai_agent, '_call_huggingface', new=AsyncMock(return_value=("Response", 5))), \
             patch.object(ai_agent, 'huggingface_api_key', "test-key"):
            tasks = [
                ai_agent.generate_response(f"Message {i}", "web_form", [])
                for i in range(5)
            ]
            responses = await asyncio.gather(*tasks)
            assert len(responses) == 5
            assert all(r is not None for r in responses)
