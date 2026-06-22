"""AI agent for generating customer support responses."""

from typing import List, Dict, Any, Optional, Tuple
import httpx
import os
import logging
import asyncio
import json
import re
from datetime import datetime

from backend.config.settings import settings

# Hugging Face Inference Client
try:
    from huggingface_hub import InferenceClient
    HF_CLIENT_AVAILABLE = True
except ImportError:
    HF_CLIENT_AVAILABLE = False
    logging.warning("huggingface_hub not installed, Hugging Face integration will not work")

logger = logging.getLogger(__name__)


# Channel-specific response configurations
CHANNEL_CONFIGS = {
    "web_form": {
        "tone": "professional and helpful",
        "max_length": 1000,
        "format": "detailed with clear structure",
        "greeting": "Thank you for contacting our AI Support Center.",
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
        knowledge_context: List[Dict[str, str]] = None,
        is_first_message: bool = True
    ) -> str:
        """
        Build system prompt based on channel and context.

        Args:
            channel: Communication channel
            knowledge_context: Relevant knowledge base entries
            is_first_message: Whether this is the first message in the session

        Returns:
            System prompt string
        """
        channel_config = CHANNEL_CONFIGS.get(channel, CHANNEL_CONFIGS["web_form"])

        greeting_instruction = f'\n- Start with: "{channel_config["greeting"]}"' if is_first_message else ""
        closing_instruction = f'\n- End with: "{channel_config["closing"]}"' if is_first_message else ""

        base_prompt = f"""You are a friendly customer support assistant. Your responses must be conversational, natural, and easy to read — like a human support agent.

FORMATTING RULES (MUST FOLLOW):
- Use plain text only. No markdown, no asterisks, no bold, no italics, no code blocks
- Keep paragraphs short — 2 to 3 sentences max, separated by a blank line
- Use natural transitions like "First...", "Also...", or "For example..." instead of lists
- Use {channel_config['format']} style
- Keep your tone {channel_config['tone']}

EXAMPLE:
"Thank you for contacting our AI Support Center. Here are the main features we offer.

We provide end-to-end security to keep your data safe. You can access your account from any device, anytime. Our team is available 24/7 if you ever need help.

Please let us know if you need further assistance."

RESPONSE STRUCTURE:{greeting_instruction}
- Use 2-3 short paragraphs separated by blank lines
- Use natural language instead of bullet points or numbered lists
- End with a friendly closing{closing_instruction}
- Maximum {channel_config['max_length']} characters

CONTENT SAFETY RULES (CRITICAL):
- Handle questions across all support categories: general inquiries, technical support, billing, feedback, and bug reports
- Politely refuse requests that ask you to: solve coding problems, write code, do school homework, or provide answers to assignments
- Politely refuse any sexual, vulgar, harassing, or illegal content
- Refusal example: "I'm here to help with questions about our products and services. Could you please ask something related to your support request?"
- Never use inappropriate, offensive, or vulgar language in your responses
- Never make up information — if unsure, be honest and offer to connect with a person
- Be empathetic, helpful, and professional at all times
- Use knowledge base info when provided"""

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
        is_first_message = not conversation_history
        system_prompt = self._get_system_prompt(channel, knowledge_context, is_first_message)

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
                    return self._strip_markdown(response), tokens, 0.9

            # Fallback to Hugging Face
            if self.huggingface_api_key:
                response, tokens = await self._call_huggingface(messages)
                if response:
                    return self._strip_markdown(response), tokens, 0.85

            # Fallback to Gemini
            if self.gemini_api_key:
                response, tokens = await self._call_gemini(message, conversation_history)
                if response:
                    return self._strip_markdown(response), tokens, 0.8

            logger.error("No AI API keys configured")
            return self._get_fallback_response(channel), 0, None

        except Exception as e:
            logger.error(f"AI generation error: {e}", exc_info=True)
            return self._get_fallback_response(channel), 0, None

    @staticmethod
    def _strip_markdown(text: str) -> str:
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        return text.strip()

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

        client = await self._get_http_client()
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
        Call Hugging Face Inference API using InferenceClient.

        Args:
            messages: Message array for chat completion

        Returns:
            Tuple of (response_text, tokens_used)
        """
        if not self.huggingface_api_key:
            return None, 0

        if not HF_CLIENT_AVAILABLE:
            logger.error("huggingface_hub library not available")
            return None, 0

        try:
            # Run the synchronous InferenceClient in a thread pool
            def _sync_call():
                client = InferenceClient(
                    model=self.huggingface_model,
                    token=self.huggingface_api_key
                )

                response = client.chat_completion(
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7
                )

                return response

            # Execute in thread pool to avoid blocking
            response = await asyncio.to_thread(_sync_call)

            # Extract the response content
            content = response.choices[0].message.content
            tokens_used = len(content.split())  # Rough estimate

            logger.info(f"Hugging Face response generated (~{tokens_used} tokens)")
            return content.strip(), tokens_used

        except Exception as e:
            logger.error(f"Hugging Face API error: {e}", exc_info=True)
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

        headers = {
            "X-Goog-Api-Key": self.gemini_api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": 0.7
            }
        }

        client = await self._get_http_client()
        try:
            response = await client.post(
                self.gemini_url,
                headers=headers,
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
