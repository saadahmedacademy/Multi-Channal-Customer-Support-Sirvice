"""AI agent for generating customer support responses."""

from typing import List, Dict, Any, Optional, Tuple
import httpx
import os
import logging
import asyncio
import json
from datetime import datetime

from backend.config.settings import settings

logger = logging.getLogger(__name__)


# Channel-specific response configurations
CHANNEL_CONFIGS = {
    "web_form": {
        "tone": "professional and helpful",
        "max_length": 1000,
        "format": "detailed with clear structure",
        "greeting": "Thank you for contacting support.",
        "closing": "Please let us know if you need further assistance."
    },
    "whatsapp": {
        "tone": "friendly and conversational",
        "max_length": 300,
        "format": "concise and direct",
        "greeting": "Hi!",
        "closing": "Let me know if you need anything else!"
    },
    "email": {
        "tone": "professional and courteous",
        "max_length": 800,
        "format": "structured with proper email format",
        "greeting": "Dear Valued Customer,",
        "closing": "Best regards,\nCustomer Support Team"
    }
}


class AIAgent:
    """AI agent for generating customer support responses."""

    def __init__(self):
        self.openrouter_api_key = settings.openrouter_api_key
        self.gemini_api_key = settings.gemini_api_key
        self.huggingface_api_key = settings.huggingface_api_key
        self.huggingface_model = settings.huggingface_model
        self.ai_model = settings.ai_model
        self.timeout = settings.ai_timeout
        self.max_tokens = settings.max_tokens

        # OpenRouter API endpoint
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

        # Gemini API endpoint
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

        # Hugging Face Standard Inference API endpoint
        self.huggingface_url = f"https://api-inference.huggingface.co/models/{self.huggingface_model}"

        # Shared HTTP client with connection pooling (reused across requests)
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create a shared HTTP client with connection pooling."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
            )
        return self._http_client

    async def close(self) -> None:
        """Close the shared HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def _get_system_prompt(
        self,
        channel: str,
        knowledge_context: List[Dict[str, str]] = None
    ) -> str:
        """
        Build system prompt based on channel and context.

        Args:
            channel: Communication channel
            knowledge_context: Relevant knowledge base entries

        Returns:
            System prompt string
        """
        channel_config = CHANNEL_CONFIGS.get(channel, CHANNEL_CONFIGS["web_form"])

        base_prompt = f"""You are a helpful AI customer support agent. Your role is to:
1. Provide accurate, helpful responses to customer inquiries
2. Use the provided knowledge base context when available
3. Maintain a {channel_config['tone']} tone
4. Keep responses {channel_config['format']} and under {channel_config['max_length']} characters

Response Guidelines:
- Start with: "{channel_config['greeting']}"
- End with: "{channel_config['closing']}"
- Be empathetic and understanding
- If you don't know something, admit it and offer to connect with a human agent
- Never make up information or provide false details"""

        if knowledge_context:
            context_text = "\n\nRelevant Knowledge Base:\n"
            for entry in knowledge_context:
                context_text += f"- {entry.get('title', 'Unknown')}: {entry.get('content', '')[:500]}\n"
            base_prompt += context_text

        return base_prompt

    async def generate_response(
        self,
        message: str,
        channel: str = "web_form",
        conversation_history: List[Dict[str, str]] = None,
        knowledge_context: List[Dict[str, str]] = None,
        customer_metadata: Dict[str, Any] = None,
        previous_channel: Optional[str] = None
    ) -> Tuple[str, int, Optional[float]]:
        """
        Generate AI response to customer message.

        Args:
            message: Customer message
            channel: Communication channel
            conversation_history: Previous messages in conversation
            knowledge_context: Relevant knowledge base entries
            customer_metadata: Customer info (timezone, language, etc.)
            previous_channel: Previous channel if cross-channel

        Returns:
            Tuple of (response_text, tokens_used, confidence_score)
        """
        system_prompt = self._get_system_prompt(channel, knowledge_context)

        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]

        # Add cross-channel acknowledgment if switching channels
        if previous_channel and previous_channel != channel:
            channel_names = {"web_form": "web form", "whatsapp": "WhatsApp", "email": "email"}
            ack_message = {
                "role": "system",
                "content": f"[Customer previously contacted us via {channel_names.get(previous_channel, 'another channel')}. Acknowledge this continuity if relevant.]"
            }
            messages.append(ack_message)

        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages

        # Add current message
        messages.append({"role": "user", "content": message})

        try:
            # Try OpenRouter first
            if self.openrouter_api_key:
                response, tokens = await self._call_openrouter(messages)
                if response:
                    return response, tokens, 0.9

            # Fallback to Hugging Face
            if self.huggingface_api_key:
                response, tokens = await self._call_huggingface(messages)
                if response:
                    return response, tokens, 0.85

            # Fallback to Gemini
            if self.gemini_api_key:
                response, tokens = await self._call_gemini(message, conversation_history)
                if response:
                    return response, tokens, 0.8

            logger.error("No AI API keys configured")
            return self._get_fallback_response(channel), 0, None

        except Exception as e:
            logger.error(f"AI generation error: {e}", exc_info=True)
            return self._get_fallback_response(channel), 0, None

    async def _call_openrouter(
        self,
        messages: List[Dict[str, str]]
    ) -> Tuple[Optional[str], int]:
        """
        Call OpenRouter API.

        Args:
            messages: Message array for chat completion

        Returns:
            Tuple of (response_text, tokens_used)
        """
        if not self.openrouter_api_key:
            return None, 0

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "AI Support Agent"
        }

        payload = {
            "model": self.ai_model,  # Use model from settings
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.7
        }

        async with await self._get_http_client() as client:
            try:
                response = await client.post(
                    self.openrouter_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)

                logger.info(f"OpenRouter response generated ({tokens_used} tokens)")
                return content.strip(), tokens_used

            except httpx.HTTPError as e:
                logger.error(f"OpenRouter API error: {e}")
                return None, 0

    async def _call_huggingface(
        self,
        messages: List[Dict[str, str]]
    ) -> Tuple[Optional[str], int]:
        """
        Call Hugging Face Standard Inference API.

        Args:
            messages: Message array for chat completion

        Returns:
            Tuple of (response_text, tokens_used)
        """
        if not self.huggingface_api_key:
            return None, 0

        headers = {
            "Authorization": f"Bearer {self.huggingface_api_key}",
            "Content-Type": "application/json"
        }

        # Convert messages to a single prompt for standard API
        prompt = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"

        prompt += "Assistant:"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": 0.7,
                "return_full_text": False
            }
        }

        async with await self._get_http_client() as client:
            try:
                response = await client.post(
                    self.huggingface_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()

                # Standard Inference API response format
                if isinstance(data, list) and len(data) > 0:
                    generated_text = data[0].get("generated_text", "")
                    tokens_used = len(generated_text.split())  # Rough estimate

                    logger.info(f"Hugging Face response generated (~{tokens_used} tokens)")
                    return generated_text.strip(), tokens_used
                else:
                    logger.warning(f"Unexpected Hugging Face response format: {data}")
                    return None, 0

            except httpx.HTTPStatusError as e:
                logger.error(f"Hugging Face API error: {e.response.status_code} - {e.response.text}")
                return None, 0

            except httpx.RequestError as e:
                logger.error(f"Hugging Face request failed: {e}")
                return None, 0

    async def _call_gemini(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Tuple[Optional[str], int]:
        """
        Call Google Gemini API.

        Args:
            message: Customer message
            conversation_history: Previous messages

        Returns:
            Tuple of (response_text, tokens_used)
        """
        if not self.gemini_api_key:
            return None, 0

        # Build prompt with history
        prompt = message
        if conversation_history:
            history_text = "\n".join([
                f"{m['role']}: {m['content']}"
                for m in conversation_history[-5:]
            ])
            prompt = f"Conversation:\n{history_text}\n\nCustomer: {message}"

        url = f"{self.gemini_url}?key={self.gemini_api_key}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": 0.7
            }
        }

        async with await self._get_http_client() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                tokens_used = len(message.split())  # Rough estimate

                logger.info(f"Gemini response generated (~{tokens_used} tokens)")
                return content.strip(), tokens_used

            except httpx.HTTPError as e:
                logger.error(f"Gemini API error: {e}")
                return None, 0

    def _get_fallback_response(self, channel: str) -> str:
        """
        Get fallback response when AI is unavailable.

        Args:
            channel: Communication channel

        Returns:
            Fallback response text
        """
        channel_config = CHANNEL_CONFIGS.get(channel, CHANNEL_CONFIGS["web_form"])

        return (
            f"{channel_config['greeting']} "
            "Thank you for your message. Our AI assistant is temporarily unavailable, "
            "but a human agent will respond to your inquiry shortly. "
            f"{channel_config['closing']}"
        )


# Global AI agent instance
ai_agent = AIAgent()
