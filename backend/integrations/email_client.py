"""Gmail API client for sending and receiving emails."""

from typing import Optional, Dict, Any, List
import base64
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from backend.config.settings import settings

logger = logging.getLogger(__name__)


# Rate limiting: 2000 emails per day (Gmail API quota)
RATE_LIMIT_MAX = 2000
RATE_LIMIT_WINDOW = timedelta(days=1)


class GmailClient:
    """Client for Gmail API integration."""

    def __init__(self):
        self.credentials = settings.gmail_credentials
        self.service_account_email = settings.gmail_service_account_email
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
        self.oauth_token = settings.gmail_oauth_token
        self.refresh_token = settings.gmail_refresh_token
        self.client_id = settings.gmail_client_id
        self.client_secret = settings.gmail_client_secret

        # Rate limiting tracking
        self._email_count = 0
        self._window_start = datetime.utcnow()

        # Configuration
        self.support_email = settings.support_email or "support@example.com"

        # Shared HTTP client with connection pooling
        self._http_client: Optional[httpx.AsyncClient] = None

        # Token refresh lock to prevent concurrent refresh attempts
        self._refreshing_token = False

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
            self._email_count = 0
            self._window_start = now

        return self._email_count < RATE_LIMIT_MAX

    def _increment_email_count(self) -> None:
        """Increment the email counter."""
        self._email_count += 1
        logger.debug(f"Gmail email count: {self._email_count}/{RATE_LIMIT_MAX}")

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self.oauth_token}",
            "Content-Type": "application/json"
        }

    async def _refresh_access_token(self) -> bool:
        """
        Refresh the OAuth access token using the refresh token.

        Returns:
            True if refresh successful, False otherwise
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            logger.error("Cannot refresh token: missing refresh_token, client_id, or client_secret")
            return False

        if self._refreshing_token:
            logger.debug("Token refresh already in progress, waiting...")
            # Wait a bit for the other refresh to complete
            import asyncio
            await asyncio.sleep(1)
            return True

        self._refreshing_token = True

        try:
            token_url = "https://oauth2.googleapis.com/token"  # nosec - OAuth2 endpoint URL, not a password
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            }

            client = await self._get_http_client()
            response = await client.post(
                token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            new_access_token = data.get("access_token")

            if not new_access_token:
                logger.error("Token refresh response missing access_token")
                return False

            # Update the token
            self.oauth_token = new_access_token
            logger.info("Gmail OAuth token refreshed successfully")

            # Note: In production, you should persist the new token to settings/database
            # For now, it will work until the worker restarts
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
        finally:
            self._refreshing_token = False

    def _encode_message(self, message: MIMEMultipart) -> str:
        """
        Encode email message as base64url.

        Args:
            message: MIME message object

        Returns:
            Base64url encoded string
        """
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return encoded

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            html: Whether body is HTML (default False)
            in_reply_to: Message-ID to reply to
            references: References header for threading

        Returns:
            Response from Gmail API
        """
        if not self.oauth_token:
            logger.warning("Gmail OAuth token not configured")
            return {"error": "Gmail not configured"}

        # Check rate limit
        if not self._check_rate_limit():
            logger.warning("Gmail rate limit exceeded")
            return {"error": "Rate limit exceeded"}

        # Create message
        message = MIMEMultipart("alternative")
        message["to"] = to_email
        message["from"] = self.support_email
        message["subject"] = subject

        # Add threading headers if provided
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
        if references:
            message["References"] = references

        # Add body
        if html:
            message.attach(MIMEText(body, "html", "utf-8"))
        else:
            message.attach(MIMEText(body, "plain", "utf-8"))

        # Encode message
        raw_message = self._encode_message(message)

        # Send via Gmail API
        endpoint = f"{self.base_url}/users/me/messages/send"
        payload = {"raw": raw_message}

        # Try sending, with automatic token refresh on 401
        for attempt in range(2):
            try:
                client = await self._get_http_client()
                response = await client.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                result = response.json()
                self._increment_email_count()

                logger.info(f"Gmail email sent to {to_email}: {result.get('id')}")
                return result

            except httpx.HTTPStatusError as e:
                # Handle 401 Unauthorized - token expired
                if e.response.status_code == 401 and attempt == 0:
                    logger.warning("Gmail token expired, attempting refresh...")
                    if await self._refresh_access_token():
                        logger.info("Token refreshed, retrying email send...")
                        continue
                    else:
                        logger.error("Token refresh failed")
                        return {"error": "Authentication failed", "status_code": 401}

                logger.error(f"Gmail API error: {e.response.status_code} - {e.response.text}")
                return {"error": str(e), "status_code": e.response.status_code}

            except httpx.RequestError as e:
                logger.error(f"Gmail request failed: {e}")
                return {"error": str(e)}

        return {"error": "Failed after retry"}

    async def send_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        original_message_id: str,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send a reply email with proper threading.

        Args:
            to_email: Recipient email address
            subject: Email subject (should start with Re:)
            body: Email body
            original_message_id: Gmail message ID being replied to
            html: Whether body is HTML

        Returns:
            Response from Gmail API
        """
        # Format subject with Re: prefix if not present
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        return await self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            html=html,
            in_reply_to=original_message_id,
            references=original_message_id
        )

    async def get_message(
        self,
        message_id: str,
        format: str = "metadata"
    ) -> Dict[str, Any]:
        """
        Get a Gmail message by ID.

        Args:
            message_id: Gmail message ID
            format: Response format (raw, metadata, minimal, full)

        Returns:
            Message data from Gmail API
        """
        if not self.oauth_token:
            return {"error": "Gmail not configured"}


        endpoint = f"{self.base_url}/users/me/messages/{message_id}"
        params = {"format": format}

        for attempt in range(2):
            try:
                client = await self._get_http_client()
                response = await client.get(
                    endpoint,
                    headers=self._get_headers(),
                    params=params,
                    timeout=30
                )
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and attempt == 0:
                    logger.warning("Gmail token expired during get_message, attempting refresh...")
                    if await self._refresh_access_token():
                        continue
                    return {"error": "Authentication failed", "status_code": 401}
                logger.error(f"Failed to get Gmail message: {e}")
                return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
            except httpx.HTTPError as e:
                logger.error(f"Failed to get Gmail message: {e}")
                return {"error": str(e)}

        return {"error": "Failed after retry"}

    async def list_messages(
        self,
        query: str = None,
        max_results: int = 10,
        label_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        List Gmail messages matching query.

        Args:
            query: Gmail search query (e.g., "from:support@example.com")
            max_results: Maximum number of results
            label_ids: Filter by label IDs

        Returns:
            List of messages
        """
        if not self.oauth_token:
            return {"error": "Gmail not configured"}


        endpoint = f"{self.base_url}/users/me/messages"
        params = {"maxResults": min(max_results, 500)}

        if query:
            params["q"] = query
        if label_ids:
            for label_id in label_ids:
                params.setdefault("labelIds", []).append(label_id)

        for attempt in range(2):
            try:
                client = await self._get_http_client()
                response = await client.get(
                    endpoint,
                    headers=self._get_headers(),
                    params=params,
                    timeout=30
                )
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and attempt == 0:
                    logger.warning("Gmail token expired during list_messages, attempting refresh...")
                    if await self._refresh_access_token():
                        continue
                    return {"error": "Authentication failed", "status_code": 401}
                logger.error(f"Failed to list Gmail messages: {e}")
                return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
            except httpx.HTTPError as e:
                logger.error(f"Failed to list Gmail messages: {e}")
                return {"error": str(e)}

        return {"error": "Failed after retry"}

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """
        Mark a message as read.

        Args:
            message_id: Gmail message ID

        Returns:
            Response from Gmail API
        """
        if not self.oauth_token:
            return {"error": "Gmail not configured"}


        endpoint = f"{self.base_url}/users/me/messages/{message_id}/modify"
        payload = {"removeLabelIds": ["UNREAD"]}

        for attempt in range(2):
            try:
                client = await self._get_http_client()
                response = await client.post(
                    endpoint,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and attempt == 0:
                    logger.warning("Gmail token expired during mark_as_read, attempting refresh...")
                    if await self._refresh_access_token():
                        continue
                    return {"error": "Authentication failed", "status_code": 401}
                logger.error(f"Failed to mark message as read: {e}")
                return {"error": str(e), "status_code": getattr(e.response, 'status_code', None)}
            except httpx.HTTPError as e:
                logger.error(f"Failed to mark message as read: {e}")
                return {"error": str(e)}

        return {"error": "Failed after retry"}

    async def add_label(self, message_id: str, label_id: str) -> Dict[str, Any]:
        """
        Add a label to a message.

        Args:
            message_id: Gmail message ID
            label_id: Label ID to add

        Returns:
            Response from Gmail API
        """
        if not self.oauth_token:
            return {"error": "Gmail not configured"}


        endpoint = f"{self.base_url}/users/me/messages/{message_id}/modify"
        payload = {"addLabelIds": [label_id]}

        try:
            client = await self._get_http_client()
            response = await client.post(
                endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to add label: {e}")
            return {"error": str(e)}

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        now = datetime.utcnow()
        window_remaining = RATE_LIMIT_WINDOW - (now - self._window_start)

        return {
            "emails_sent": self._email_count,
            "emails_remaining": max(0, RATE_LIMIT_MAX - self._email_count),
            "window_resets_in": str(window_remaining),
            "limit": RATE_LIMIT_MAX
        }

    def is_configured(self) -> bool:
        """Check if Gmail client is configured."""
        return bool(self.oauth_token)


# Global Gmail client instance
gmail_client = GmailClient()
