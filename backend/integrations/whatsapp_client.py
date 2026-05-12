"""WhatsApp Cloud API client for sending and receiving messages."""

from typing import Optional, Dict, Any, List
import httpx
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from backend.config.settings import settings

logger = logging.getLogger(__name__)


# Rate limiting: 1000 messages per 24h window (Meta free tier)
RATE_LIMIT_MAX = 1000
RATE_LIMIT_WINDOW = timedelta(hours=24)


class WhatsAppClient:
    """Client for Meta WhatsApp Cloud API."""

    def __init__(self):
        self.access_token = settings.meta_whatsapp_token
        self.phone_id = settings.meta_whatsapp_phone_id
        self.business_id = settings.meta_whatsapp_business_id
        self.base_url = "https://graph.facebook.com/v17.0"

        # Rate limiting tracking
        self._message_count = 0
        self._window_start = datetime.utcnow()

        # Shared HTTP client with connection pooling
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create a shared HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=3),
            )
        return self._http_client

    async def close(self) -> None:
        """Close the shared HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.
        
        Returns:
            True if within limits, False if exceeded
        """
        now = datetime.utcnow()
        
        # Reset counter if window expired
        if now - self._window_start > RATE_LIMIT_WINDOW:
            self._message_count = 0
            self._window_start = now
        
        return self._message_count < RATE_LIMIT_MAX

    def _increment_message_count(self) -> None:
        """Increment the message counter."""
        self._message_count += 1
        logger.debug(f"WhatsApp message count: {self._message_count}/{RATE_LIMIT_MAX}")

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def send_text_message(
        self,
        to_phone: str,
        message: str,
        reply_to_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.

        Args:
            to_phone: Recipient phone number (E.164 format)
            message: Message text (max 4096 characters)
            reply_to_id: Optional message ID to reply to

        Returns:
            Response from WhatsApp API
        """
        if not self.access_token:
            logger.warning("WhatsApp access token not configured")
            return {"error": "WhatsApp not configured"}

        # Check rate limit
        if not self._check_rate_limit():
            logger.warning("WhatsApp rate limit exceeded")
            return {"error": "Rate limit exceeded"}

        # Validate message length (WhatsApp limit: 4096 chars, but we use 300 for conversational)
        if len(message) > 4096:
            message = message[:4093] + "..."

        endpoint = f"{self.base_url}/{self.phone_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {
                "body": message,
                "preview_url": True
            }
        }

        # Add reply context if provided
        if reply_to_id:
            payload["context"] = {"message_id": reply_to_id}

        try:
            async with await self._get_http_client() as client:
                response = await client.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                result = response.json()
                self._increment_message_count()

                logger.info(f"WhatsApp message sent to {to_phone}: {result.get('messages', [{}])[0].get('id')}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            return {"error": str(e), "status_code": e.response.status_code}
        
        except httpx.RequestError as e:
            logger.error(f"WhatsApp request failed: {e}")
            return {"error": str(e)}

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a template message (for outbound notifications).

        Args:
            to_phone: Recipient phone number
            template_name: Name of approved template
            language: Template language code
            components: Optional template components

        Returns:
            Response from WhatsApp API
        """
        if not self.access_token:
            return {"error": "WhatsApp not configured"}

        if not self._check_rate_limit():
            return {"error": "Rate limit exceeded"}

        endpoint = f"{self.base_url}/{self.phone_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                }
            }
        }

        if components:
            payload["template"]["components"] = components

        try:
            async with await self._get_http_client() as client:
                response = await client.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                result = response.json()
                self._increment_message_count()

                return result

        except httpx.HTTPError as e:
            logger.error(f"WhatsApp template message failed: {e}")
            return {"error": str(e)}

    async def mark_message_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read.

        Args:
            message_id: WhatsApp message ID to mark as read

        Returns:
            Response from WhatsApp API
        """
        if not self.access_token:
            return {"error": "WhatsApp not configured"}

        endpoint = f"{self.base_url}/{self.phone_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            async with await self._get_http_client() as client:
                response = await client.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to mark message as read: {e}")
            return {"error": str(e)}

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        now = datetime.utcnow()
        window_remaining = RATE_LIMIT_WINDOW - (now - self._window_start)
        
        return {
            "messages_sent": self._message_count,
            "messages_remaining": max(0, RATE_LIMIT_MAX - self._message_count),
            "window_resets_in": str(window_remaining),
            "limit": RATE_LIMIT_MAX
        }


# Global WhatsApp client instance
whatsapp_client = WhatsAppClient()
