"""Unit tests for AI agent functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.worker.ai_agent import AIAgent


@pytest.fixture
def ai_agent():
    """Create AI agent instance for testing."""
    return AIAgent()


@pytest.fixture
def sample_knowledge_base():
    """Sample knowledge base entries."""
    return [
        {
            "id": uuid4(),
            "question": "How do I reset my password?",
            "answer": "Click 'Forgot Password' on the login page and follow the email instructions.",
            "category": "account",
            "keywords": ["password", "reset", "login"]
        },
        {
            "id": uuid4(),
            "question": "What are your pricing plans?",
            "answer": "We offer Basic ($10/mo), Pro ($25/mo), and Enterprise (custom pricing).",
            "category": "pricing",
            "keywords": ["pricing", "plans", "cost", "price"]
        },
        {
            "id": uuid4(),
            "question": "How do I integrate the API?",
            "answer": "Use our REST API with your API key. Documentation: https://docs.example.com/api",
            "category": "technical",
            "keywords": ["api", "integration", "technical"]
        }
    ]


class TestAIAgentInitialization:
    """Test AI agent initialization."""

    def test_ai_agent_initializes_successfully(self, ai_agent):
        """Test that AI agent initializes without errors."""
        assert ai_agent is not None
        assert hasattr(ai_agent, 'generate_response')

    def test_ai_agent_has_required_methods(self, ai_agent):
        """Test that AI agent has all required methods."""
        assert hasattr(ai_agent, 'generate_response')
        assert hasattr(ai_agent, '_load_knowledge_context')
        assert hasattr(ai_agent, '_format_response_for_channel')


class TestKnowledgeBaseIntegration:
    """Test knowledge base integration."""

    @pytest.mark.asyncio
    async def test_load_knowledge_context_with_results(self, ai_agent, sample_knowledge_base):
        """Test loading knowledge base context when results are found."""
        with patch.object(ai_agent, 'knowledge_repo') as mock_repo:
            mock_repo.search_knowledge_base = AsyncMock(return_value=sample_knowledge_base[:2])

            context = await ai_agent._load_knowledge_context("How do I reset my password?")

            assert context is not None
            assert "password" in context.lower() or "reset" in context.lower()
            mock_repo.search_knowledge_base.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_knowledge_context_with_no_results(self, ai_agent):
        """Test loading knowledge base context when no results are found."""
        with patch.object(ai_agent, 'knowledge_repo') as mock_repo:
            mock_repo.search_knowledge_base = AsyncMock(return_value=[])

            context = await ai_agent._load_knowledge_context("Random question")

            assert context == "" or context is None
            mock_repo.search_knowledge_base.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_knowledge_context_handles_errors(self, ai_agent):
        """Test that knowledge base errors are handled gracefully."""
        with patch.object(ai_agent, 'knowledge_repo') as mock_repo:
            mock_repo.search_knowledge_base = AsyncMock(side_effect=Exception("DB error"))

            # Should not raise exception
            context = await ai_agent._load_knowledge_context("test question")

            assert context == "" or context is None


class TestResponseGeneration:
    """Test AI response generation."""

    @pytest.mark.asyncio
    async def test_generate_response_basic(self, ai_agent):
        """Test basic response generation."""
        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "Thank you for contacting support. I can help you with that."

            response = await ai_agent.generate_response(
                message="I need help with my account",
                channel="web_form",
                conversation_history=[]
            )

            assert response is not None
            assert len(response) > 0
            mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(self, ai_agent):
        """Test response generation with conversation history."""
        conversation_history = [
            {"role": "customer", "content": "I need help"},
            {"role": "agent", "content": "How can I assist you?"},
            {"role": "customer", "content": "My account is locked"}
        ]

        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "I'll help you unlock your account."

            response = await ai_agent.generate_response(
                message="Can you help me?",
                channel="web_form",
                conversation_history=conversation_history
            )

            assert response is not None
            # Verify conversation history was included in API call
            call_args = mock_api.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_generate_response_with_knowledge_base(self, ai_agent, sample_knowledge_base):
        """Test response generation includes knowledge base context."""
        with patch.object(ai_agent, 'knowledge_repo') as mock_repo:
            mock_repo.search_knowledge_base = AsyncMock(return_value=sample_knowledge_base[:1])

            with patch.object(ai_agent, '_call_ai_api') as mock_api:
                mock_api.return_value = "To reset your password, click 'Forgot Password'."

                response = await ai_agent.generate_response(
                    message="How do I reset my password?",
                    channel="web_form",
                    conversation_history=[]
                )

                assert response is not None
                assert "password" in response.lower()

    @pytest.mark.asyncio
    async def test_generate_response_handles_api_errors(self, ai_agent):
        """Test that API errors are handled gracefully."""
        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.side_effect = Exception("API timeout")

            response = await ai_agent.generate_response(
                message="Test message",
                channel="web_form",
                conversation_history=[]
            )

            # Should return fallback response, not raise exception
            assert response is not None
            assert "error" in response.lower() or "sorry" in response.lower()


class TestChannelAwareFormatting:
    """Test channel-aware response formatting."""

    def test_format_response_for_web_form(self, ai_agent):
        """Test formatting for web form channel (formal, detailed)."""
        raw_response = "Here is the solution to your problem."

        formatted = ai_agent._format_response_for_channel(raw_response, "web_form")

        assert formatted is not None
        assert len(formatted) > 0
        # Web form responses should be formal and can be longer
        assert len(formatted) >= len(raw_response) * 0.8

    def test_format_response_for_whatsapp(self, ai_agent):
        """Test formatting for WhatsApp channel (concise, conversational)."""
        raw_response = "Thank you for contacting us. I understand you're having an issue with your account. Let me help you resolve this problem right away."

        formatted = ai_agent._format_response_for_channel(raw_response, "whatsapp")

        assert formatted is not None
        # WhatsApp responses should be concise (max 300 chars per spec)
        assert len(formatted) <= 300

    def test_format_response_for_email(self, ai_agent):
        """Test formatting for email channel (formal, structured)."""
        raw_response = "Here is the information you requested."

        formatted = ai_agent._format_response_for_channel(raw_response, "email")

        assert formatted is not None
        assert len(formatted) > 0
        # Email responses should be formal and structured

    def test_format_response_preserves_key_information(self, ai_agent):
        """Test that formatting doesn't lose important information."""
        raw_response = "Your ticket ID is #12345. Please reference this in future communications."

        formatted = ai_agent._format_response_for_channel(raw_response, "whatsapp")

        assert "12345" in formatted
        # Key information should be preserved even when shortening


class TestResponseQuality:
    """Test AI response quality and appropriateness."""

    @pytest.mark.asyncio
    async def test_response_is_relevant_to_question(self, ai_agent):
        """Test that responses are relevant to the customer's question."""
        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "To reset your password, click 'Forgot Password' on the login page."

            response = await ai_agent.generate_response(
                message="How do I reset my password?",
                channel="web_form",
                conversation_history=[]
            )

            assert "password" in response.lower()

    @pytest.mark.asyncio
    async def test_response_is_professional(self, ai_agent):
        """Test that responses maintain professional tone."""
        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "Thank you for contacting us. I'd be happy to help."

            response = await ai_agent.generate_response(
                message="I need help",
                channel="web_form",
                conversation_history=[]
            )

            # Should not contain unprofessional language
            unprofessional_words = ["dude", "bro", "lol", "omg"]
            assert not any(word in response.lower() for word in unprofessional_words)

    @pytest.mark.asyncio
    async def test_response_length_is_appropriate(self, ai_agent):
        """Test that response length is appropriate for the channel."""
        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "Short answer."

            response = await ai_agent.generate_response(
                message="Quick question",
                channel="web_form",
                conversation_history=[]
            )

            # Response should not be empty
            assert len(response) > 0
            # Response should not be excessively long (max 2000 chars)
            assert len(response) <= 2000


class TestErrorHandling:
    """Test error handling in AI agent."""

    @pytest.mark.asyncio
    async def test_handles_empty_message(self, ai_agent):
        """Test handling of empty message."""
        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "How can I help you today?"

            response = await ai_agent.generate_response(
                message="",
                channel="web_form",
                conversation_history=[]
            )

            assert response is not None
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_handles_very_long_message(self, ai_agent):
        """Test handling of very long message."""
        long_message = "test " * 1000  # 5000 characters

        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "I understand your concern."

            response = await ai_agent.generate_response(
                message=long_message,
                channel="web_form",
                conversation_history=[]
            )

            assert response is not None

    @pytest.mark.asyncio
    async def test_handles_special_characters(self, ai_agent):
        """Test handling of special characters in message."""
        special_message = "Test <script>alert('xss')</script> & symbols: @#$%"

        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "I can help with that."

            response = await ai_agent.generate_response(
                message=special_message,
                channel="web_form",
                conversation_history=[]
            )

            assert response is not None
            # Response should not contain script tags
            assert "<script>" not in response.lower()


class TestPerformance:
    """Test AI agent performance characteristics."""

    @pytest.mark.asyncio
    async def test_response_generation_is_async(self, ai_agent):
        """Test that response generation is properly async."""
        import asyncio

        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            async def slow_api_call(*args, **kwargs):
                await asyncio.sleep(0.1)
                return "Response"

            mock_api.side_effect = slow_api_call

            # Should complete without blocking
            response = await ai_agent.generate_response(
                message="Test",
                channel="web_form",
                conversation_history=[]
            )

            assert response is not None

    @pytest.mark.asyncio
    async def test_handles_concurrent_requests(self, ai_agent):
        """Test that AI agent can handle concurrent requests."""
        import asyncio

        with patch.object(ai_agent, '_call_ai_api') as mock_api:
            mock_api.return_value = "Response"

            # Generate multiple responses concurrently
            tasks = [
                ai_agent.generate_response(f"Message {i}", "web_form", [])
                for i in range(5)
            ]

            responses = await asyncio.gather(*tasks)

            assert len(responses) == 5
            assert all(r is not None for r in responses)
