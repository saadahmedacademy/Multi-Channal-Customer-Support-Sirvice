"""Comprehensive unit tests for AI agent functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import httpx

from backend.worker.ai_agent import AIAgent, CHANNEL_CONFIGS


@pytest.fixture
def ai_agent():
    """Create AI agent instance for testing."""
    return AIAgent()


@pytest.fixture
def sample_knowledge_context():
    """Sample knowledge base context."""
    return [
        {
            "title": "Password Reset",
            "content": "Click 'Forgot Password' on the login page and follow the email instructions."
        },
        {
            "title": "Pricing Plans",
            "content": "We offer Basic ($10/mo), Pro ($25/mo), and Enterprise (custom pricing)."
        }
    ]


class TestAIAgentInitialization:
    """Test AI agent initialization."""

    def test_ai_agent_initializes_successfully(self, ai_agent):
        """Test that AI agent initializes without errors."""
        assert ai_agent is not None
        assert hasattr(ai_agent, 'generate_response')
        assert ai_agent._http_client is None  # Not created until first use

    def test_channel_configs_exist(self):
        """Test that channel configurations are defined."""
        assert "web_form" in CHANNEL_CONFIGS
        assert "whatsapp" in CHANNEL_CONFIGS
        assert "email" in CHANNEL_CONFIGS

    def test_web_form_channel_config(self):
        """Test web form channel configuration."""
        config = CHANNEL_CONFIGS["web_form"]
        assert config["tone"] == "professional and helpful"
        assert config["max_length"] == 1000
        assert "greeting" in config
        assert "closing" in config

    def test_whatsapp_channel_config(self):
        """Test WhatsApp channel configuration."""
        config = CHANNEL_CONFIGS["whatsapp"]
        assert config["tone"] == "friendly and conversational"
        assert config["max_length"] == 300
        assert config["greeting"] == "Hi!"


class TestSystemPromptGeneration:
    """Test system prompt generation."""

    def test_get_system_prompt_basic(self, ai_agent):
        """Test basic system prompt generation."""
        prompt = ai_agent._get_system_prompt("web_form")
        assert "professional and helpful" in prompt
        assert "1000 characters" in prompt

    def test_get_system_prompt_with_knowledge(self, ai_agent, sample_knowledge_context):
        """Test system prompt with knowledge base context."""
        prompt = ai_agent._get_system_prompt("web_form", sample_knowledge_context)
        assert "Relevant Knowledge Base" in prompt
        assert "Password Reset" in prompt
        assert "Pricing Plans" in prompt

    def test_get_system_prompt_whatsapp(self, ai_agent):
        """Test WhatsApp-specific system prompt."""
        prompt = ai_agent._get_system_prompt("whatsapp")
        assert "friendly and conversational" in prompt
        assert "300 characters" in prompt
        assert "Hi!" in prompt

    def test_get_system_prompt_email(self, ai_agent):
        """Test email-specific system prompt."""
        prompt = ai_agent._get_system_prompt("email")
        assert "professional and courteous" in prompt
        assert "800 characters" in prompt





class TestHuggingFaceAPI:
    """Test Hugging Face API integration."""

    @pytest.mark.asyncio
    async def test_call_huggingface_success(self, ai_agent):
        """Test successful Hugging Face API call."""
        with patch.object(ai_agent, '_get_http_client') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{
                    "message": {"content": "HuggingFace response"}
                }]
            }
            mock_response.raise_for_status = MagicMock()

            mock_http = AsyncMock()
            mock_http.post = AsyncMock(return_value=mock_response)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock()
            mock_client.return_value = mock_http

            messages = [{"role": "user", "content": "Hello"}]
            response, tokens = await ai_agent._call_huggingface(messages)

            assert response == "HuggingFace response"
            assert tokens > 0

    @pytest.mark.asyncio
    async def test_call_huggingface_no_api_key(self, ai_agent):
        """Test HuggingFace call without API key."""
        ai_agent.huggingface_api_key = None
        messages = [{"role": "user", "content": "Hello"}]
        response, tokens = await ai_agent._call_huggingface(messages)

        assert response is None
        assert tokens == 0

    @pytest.mark.asyncio
    async def test_call_huggingface_model_loading(self, ai_agent):
        """Test HuggingFace model loading (503 error with retry)."""
        with patch.object(ai_agent, '_get_http_client') as mock_client:
            mock_response_503 = MagicMock()
            mock_response_503.status_code = 503
            mock_response_503.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError("Model loading", request=MagicMock(), response=mock_response_503)
            )

            mock_response_200 = MagicMock()
            mock_response_200.json.return_value = {
                "choices": [{
                    "message": {"content": "Response after loading"}
                }]
            }
            mock_response_200.raise_for_status = MagicMock()

            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=[mock_response_503, mock_response_200])
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock()
            mock_client.return_value = mock_http

            with patch('asyncio.sleep', new_callable=AsyncMock):
                messages = [{"role": "user", "content": "Hello"}]
                response, tokens = await ai_agent._call_huggingface(messages)

                assert response == "Response after loading"


class TestGenerateResponse:
    """Test main generate_response method."""

    @pytest.mark.asyncio
    async def test_generate_response_no_api_keys(self, ai_agent):
        """Test response generation when no API keys are configured."""
        ai_agent.huggingface_api_key = None

        response, tokens, confidence = await ai_agent.generate_response(
            message="Hello",
            channel="web_form"
        )

        assert "temporarily unavailable" in response
        assert tokens == 0
        assert confidence is None

    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(self, ai_agent):
        """Test response generation with conversation history."""
        with patch.object(ai_agent, '_call_huggingface', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ("Response with context", 50)

            history = [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"}
            ]

            response, tokens, confidence = await ai_agent.generate_response(
                message="Follow-up question",
                channel="web_form",
                conversation_history=history
            )

            assert response == "Response with context"
            assert tokens == 50
            assert confidence == 0.85

    @pytest.mark.asyncio
    async def test_generate_response_cross_channel(self, ai_agent):
        """Test response generation with cross-channel acknowledgment."""
        with patch.object(ai_agent, '_call_huggingface', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ("Cross-channel response", 40)

            response, tokens, confidence = await ai_agent.generate_response(
                message="New message",
                channel="whatsapp",
                previous_channel="web_form"
            )

            assert response == "Cross-channel response"
            call_args = mock_call.call_args[0][0]
            assert any("previously contacted" in str(msg.get("content", "")).lower() for msg in call_args)


class TestFallbackResponse:
    """Test fallback response generation."""

    def test_fallback_response_web_form(self, ai_agent):
        """Test fallback response for web form."""
        response = ai_agent._get_fallback_response("web_form")
        assert "Thank you" in response
        assert "temporarily unavailable" in response
        assert "human agent" in response

    def test_fallback_response_whatsapp(self, ai_agent):
        """Test fallback response for WhatsApp."""
        response = ai_agent._get_fallback_response("whatsapp")
        assert "Hi!" in response
        assert "temporarily unavailable" in response

    def test_fallback_response_email(self, ai_agent):
        """Test fallback response for email."""
        response = ai_agent._get_fallback_response("email")
        assert "Dear Valued Customer" in response
        assert "temporarily unavailable" in response


class TestHTTPClientManagement:
    """Test HTTP client lifecycle management."""

    @pytest.mark.asyncio
    async def test_get_http_client_creates_new(self, ai_agent):
        """Test that HTTP client is created on first use."""
        assert ai_agent._http_client is None
        client = await ai_agent._get_http_client()
        assert client is not None
        assert ai_agent._http_client is not None

    @pytest.mark.asyncio
    async def test_get_http_client_reuses_existing(self, ai_agent):
        """Test that HTTP client is reused."""
        client1 = await ai_agent._get_http_client()
        client2 = await ai_agent._get_http_client()
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_close_http_client(self, ai_agent):
        """Test HTTP client cleanup."""
        client = await ai_agent._get_http_client()
        assert ai_agent._http_client is not None

        await ai_agent.close()
        assert ai_agent._http_client is None


class TestErrorHandling:
    """Test error handling in AI agent."""

    @pytest.mark.asyncio
    async def test_generate_response_exception_handling(self, ai_agent):
        """Test that exceptions are caught and fallback is returned."""
        with patch.object(ai_agent, '_call_huggingface', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Unexpected error")

            response, tokens, confidence = await ai_agent.generate_response(
                message="Test",
                channel="web_form"
            )

            assert "temporarily unavailable" in response
            assert tokens == 0
            assert confidence is None

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, ai_agent):
        """Test handling of API timeouts."""
        with patch.object(ai_agent, '_get_http_client') as mock_client:
            mock_http = AsyncMock()
            mock_http.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock()
            mock_client.return_value = mock_http

            messages = [{"role": "user", "content": "Hello"}]
            response, tokens = await ai_agent._call_huggingface(messages)

            assert response is None
            assert tokens == 0
