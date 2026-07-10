"""AI agent for generating customer support responses via Hugging Face Inference API."""

from typing import List, Dict, Any, Optional, Tuple
import httpx
import logging
import re

from backend.config.settings import settings

logger = logging.getLogger(__name__)


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
    """AI agent for generating customer support responses via Hugging Face."""

    def __init__(self):
        self.huggingface_api_key = settings.huggingface_api_key
        self.huggingface_model = settings.huggingface_model
        self.timeout = settings.ai_timeout
        self.max_tokens = settings.max_tokens
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
            )
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def _get_system_prompt(
        self,
        channel: str,
        knowledge_context: List[Dict[str, str]] = None,
        is_first_message: bool = True
    ) -> str:
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
        is_first_message = not conversation_history
        system_prompt = self._get_system_prompt(channel, knowledge_context, is_first_message)

        messages = [{"role": "system", "content": system_prompt}]

        if previous_channel and previous_channel != channel:
            channel_names = {"web_form": "web form", "whatsapp": "WhatsApp", "email": "email"}
            ack_message = {
                "role": "system",
                "content": f"[Customer previously contacted us via {channel_names.get(previous_channel, 'another channel')}. Acknowledge this continuity if relevant.]"
            }
            messages.append(ack_message)

        if conversation_history:
            messages.extend(conversation_history[-10:])

        messages.append({"role": "user", "content": message})

        try:
            if self.huggingface_api_key:
                response, tokens = await self._call_huggingface(messages)
                if response:
                    return self._strip_markdown(response), tokens, 0.85

            logger.error("HUGGINGFACE_API_KEY not configured")
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

    async def _call_huggingface(
        self,
        messages: List[Dict[str, str]]
    ) -> Tuple[Optional[str], int]:
        if not self.huggingface_api_key:
            return None, 0

        models_to_try = [
            self.huggingface_model,
            "NousResearch/Hermes-3-Llama-3.1-8B",
            "Qwen/Qwen2.5-7B-Instruct",
        ]

        client = await self._get_http_client()

        for model in models_to_try:
            try:
                url = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
                response = await client.post(
                    url,
                    json={
                        "messages": messages,
                        "max_tokens": self.max_tokens,
                        "temperature": 0.7,
                    },
                    headers={
                        "Authorization": f"Bearer {self.huggingface_api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.timeout,
                )

                if response.status_code == 503:
                    logger.warning(f"HF model {model} is loading (503), trying next...")
                    continue

                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = len(content.split())
                logger.info(f"Hugging Face ({model}) response generated (~{tokens_used} tokens)")
                return content.strip(), tokens_used

            except httpx.HTTPStatusError as e:
                logger.warning(f"HF model {model} failed ({e.response.status_code}): {e.response.text[:200]}")
                continue
            except Exception as e:
                logger.warning(f"HF model {model} error: {e}")
                continue

        logger.error("All Hugging Face models failed")
        return None, 0

    def _get_fallback_response(self, channel: str) -> str:
        channel_config = CHANNEL_CONFIGS.get(channel, CHANNEL_CONFIGS["web_form"])

        return (
            f"{channel_config['greeting']} "
            "Thank you for your message. Our AI assistant is temporarily unavailable, "
            "but a human agent will respond to your inquiry shortly. "
            f"{channel_config['closing']}"
        )


ai_agent = AIAgent()
