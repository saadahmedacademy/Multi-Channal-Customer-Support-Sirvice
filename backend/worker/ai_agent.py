"""AI agent for generating customer support responses."""

from typing import List, Dict, Any, Optional, Tuple
import httpx
import os
import logging
import asyncio
import json
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

    def _format_conversational(self, text: str) -> str:
        """
        Convert markdown bullet points into natural conversational paragraphs.

        Args:
            text: Response text that may contain bullet points

        Returns:
            Formatted conversational text without markdown
        """
        import re

        # Remove common list introductions
        text = re.sub(r'(?:Our (?:service|main features|platform) (?:offers|includes?|provides?)[:\s]*\n+)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:Here (?:are|is) (?:a few|some) (?:reasons|benefits|features)[:\s]*\n+)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:(?:With|Using) our (?:service|platform), you can[:\s]*\n+)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(?:As for .*?, here (?:are|is)[:\s]*\n+)', '', text, flags=re.IGNORECASE)

        # Split into lines
        lines = text.split('\n')
        formatted_lines = []
        bullet_items = []
        in_bullet_section = False

        for line in lines:
            stripped = line.strip()

            # Check if line is a bullet point
            if re.match(r'^[\*\-\•]\s+', stripped):
                in_bullet_section = True
                # Extract content after bullet
                content = re.sub(r'^[\*\-\•]\s+', '', stripped).strip()
                # Remove trailing punctuation for cleaner joining
                content = re.sub(r'[,;]$', '', content)
                bullet_items.append(content)
            else:
                # If we have accumulated bullet items, convert them to sentences
                if bullet_items:
                    # Create natural flowing text from bullet items
                    if len(bullet_items) == 1:
                        natural_text = f"We offer {bullet_items[0].lower()}."
                    elif len(bullet_items) == 2:
                        natural_text = f"We offer {bullet_items[0].lower()} and {bullet_items[1].lower()}."
                    elif len(bullet_items) == 3:
                        natural_text = f"We offer {bullet_items[0].lower()}, {bullet_items[1].lower()}, and {bullet_items[2].lower()}."
                    else:
                        # Group into 2-3 sentences for readability
                        mid = len(bullet_items) // 2
                        first_group = ', '.join([item.lower() for item in bullet_items[:mid]])
                        second_group = ', and '.join([item.lower() for item in bullet_items[mid:]])
                        natural_text = f"We offer {first_group}. You'll also get {second_group}."

                    formatted_lines.append(natural_text)
                    bullet_items = []
                    in_bullet_section = False

                # Add the non-bullet line if it's not empty
                if stripped and not re.match(r'(?:Our|Here|With|As for)', stripped, re.IGNORECASE):
                    formatted_lines.append(stripped)

        # Handle remaining bullet items at end
        if bullet_items:
            if len(bullet_items) == 1:
                natural_text = f"We offer {bullet_items[0].lower()}."
            elif len(bullet_items) == 2:
                natural_text = f"We offer {bullet_items[0].lower()} and {bullet_items[1].lower()}."
            else:
                mid = len(bullet_items) // 2
                first_group = ', '.join([item.lower() for item in bullet_items[:mid]])
                second_group = ', and '.join([item.lower() for item in bullet_items[mid:]])
                natural_text = f"We offer {first_group}. You'll also get {second_group}."
            formatted_lines.append(natural_text)

        # Join lines into paragraphs
        result = '\n\n'.join(formatted_lines)

        return result

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

        base_prompt = f"""You are a friendly customer support assistant. CRITICAL: You must write in plain conversational paragraphs ONLY, exactly like ChatGPT or Claude.

FORMATTING RULES (MUST FOLLOW):
- Write ONLY in plain text paragraphs
- NEVER use asterisks (*), dashes (-), or bullet points
- NEVER use markdown syntax (no **, no _, no #)
- NEVER create lists with special characters
- Write like you're texting a friend - natural and conversational
- Keep your tone {channel_config['tone']}

CORRECT EXAMPLE:
"Our service provides great security, easy access from anywhere, and personalized recommendations. You'll also get 24/7 support whenever you need help. Everything is designed to make your experience smooth and enjoyable."

WRONG EXAMPLE (DO NOT DO THIS):
"Our service offers:
* Great security
* Easy access
* Personalized recommendations"

HOW TO STRUCTURE YOUR RESPONSE:
- Start with: "{channel_config['greeting']}"
- Write 2-3 short paragraphs that flow naturally
- Weave multiple points into sentences instead of listing them
- Use "and", "also", "plus" to connect ideas smoothly
- End with: "{channel_config['closing']}"
- Maximum {channel_config['max_length']} characters

IMPORTANT:
- If unsure, be honest and offer to connect them with a person
- Never make up information
- Use knowledge base info when provided
- Be empathetic and helpful"""

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
                    formatted_response = self._format_conversational(response)
                    return formatted_response, tokens, 0.9

            # Fallback to Hugging Face
            if self.huggingface_api_key:
                response, tokens = await self._call_huggingface(messages)
                if response:
                    logger.info(f"Raw HF response: {response[:200]}...")
                    formatted_response = self._format_conversational(response)
                    logger.info(f"Formatted response: {formatted_response[:200]}...")
                    return formatted_response, tokens, 0.85

            # Fallback to Gemini
            if self.gemini_api_key:
                response, tokens = await self._call_gemini(message, conversation_history)
                if response:
                    formatted_response = self._format_conversational(response)
                    return formatted_response, tokens, 0.8

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
