"""WhatsApp webhook endpoints for receiving messages and status updates."""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import PlainTextResponse
import hashlib
import hmac
import logging
import os
from typing import Dict, Any

from backend.config.settings import settings
from backend.integrations.queue_client import queue_client, TOPICS
from backend.db.connection import db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])


def verify_whatsapp_signature(
    payload: bytes,
    signature: str,
) -> bool:
    """
    Verify X-Hub-Signature-256 from WhatsApp webhook.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid
    """
    app_secret = settings.whatsapp_app_secret
    if not app_secret:
        logger.warning("WHATSAPP_APP_SECRET not configured — skipping webhook signature verification")
        return True

    try:
        # Signature format: sha256=<hex_string>
        if not signature.startswith("sha256="):
            return False

        expected_hash = signature[7:]  # Remove "sha256=" prefix

        # Calculate HMAC-SHA256 using the stable App Secret from Meta dashboard
        computed_hash = hmac.new(
            app_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_hash, computed_hash)

    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


@router.get("/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """
    WhatsApp webhook verification (GET).

    Meta sends a GET request to verify the webhook URL during setup.

    Query params (from Meta):
        hub.mode: 'subscribe'
        hub.verify_token: Your verify token
        hub.challenge: Random string to echo back
    """
    query_params = request.query_params

    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    # Expected verify token from settings
    expected_token = settings.whatsapp_verify_token

    if mode == "subscribe" and token == expected_token:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=challenge)

    logger.warning(f"WhatsApp webhook verification failed: mode={mode}, token={token}")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed"
    )


@router.post("/whatsapp")
async def whatsapp_webhook_receive(request: Request):
    """
    WhatsApp webhook for receiving messages (POST).

    Handles incoming messages, delivery receipts, and read receipts.
    """
    # Get signature header
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature (skip in development)
    if settings.is_production and not verify_whatsapp_signature(body, signature):
        logger.error("Invalid WhatsApp webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Parse JSON payload
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse WhatsApp webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )

    logger.debug(f"WhatsApp webhook received: {data}")

    # Handle different event types
    if "entry" not in data:
        return PlainTextResponse(content="EVENT_RECEIVED")

    # Process each entry
    for entry in data["entry"]:
        # Get WhatsApp business account ID
        business_account_id = entry.get("id")
        
        # Process changes
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})

            if field == "messages":
                await _process_messages(value, business_account_id)
            elif field in ("message_template_status_update", "message_template_quality_update"):
                await _process_template_updates(value, field)

    return PlainTextResponse(content="EVENT_RECEIVED")


async def _process_messages(
    value: Dict[str, Any],
    business_account_id: str
) -> None:
    """
    Process incoming WhatsApp messages.

    Args:
        value: Message data from webhook
        business_account_id: WhatsApp business account ID
    """
    # Handle incoming messages
    if "messages" in value:
        for message in value["messages"]:
            await _handle_incoming_message(message, business_account_id)

    # Handle status updates (delivered, read, etc.)
    if "statuses" in value:
        for status_update in value["statuses"]:
            await _handle_status_update(status_update)


async def _handle_incoming_message(
    message: Dict[str, Any],
    business_account_id: str
) -> None:
    """
    Handle a single incoming WhatsApp message.

    Args:
        message: WhatsApp message object
        business_account_id: Business account ID
    """
    message_type = message.get("type")
    from_phone = message.get("from")
    message_id = message.get("id")
    timestamp = message.get("timestamp")

    logger.info(f"Received WhatsApp {message_type} from {from_phone}")

    # Extract message content based on type
    content = None
    if message_type == "text":
        content = message.get("text", {}).get("body", "")
    elif message_type == "image":
        content = "[Image received]"
        # Could download image from message["image"]["id"]
    elif message_type == "document":
        content = "[Document received]"
    elif message_type == "audio":
        content = "[Audio message received]"
    elif message_type == "voice":
        content = "[Voice message received]"
    else:
        content = f"[Unsupported message type: {message_type}]"

    # Create customer message payload
    customer_message = {
        "type": "whatsapp_message",
        "channel": "whatsapp",
        "from_phone": from_phone,
        "message_id": message_id,
        "timestamp": timestamp,
        "content": content,
        "message_type": message_type,
        "business_account_id": business_account_id
    }

    # Queue for processing
    try:
        await queue_client.publish(
            topic=TOPICS["tickets_incoming"],
            message=customer_message,
            key=from_phone
        )
        logger.info(f"WhatsApp message queued: {message_id}")
    except Exception as e:
        logger.error(f"Failed to queue WhatsApp message: {e}")


async def _handle_status_update(status_update: Dict[str, Any]) -> None:
    """
    Handle message status updates (sent, delivered, read, failed).

    Args:
        status_update: Status object from webhook
    """
    message_id = status_update.get("id")
    status_type = status_update.get("status")
    recipient_id = status_update.get("recipient_id")
    timestamp = status_update.get("timestamp")

    logger.info(f"WhatsApp message {message_id} status: {status_type}")

    # Update delivery status in database
    try:
        async with db.acquire() as conn:
            await conn.execute("""
                UPDATE messages
                SET delivery_status = $1
                WHERE channel_message_id = $2
            """, status_type, message_id)
        
        logger.debug(f"Updated delivery status for {message_id} to {status_type}")
    except Exception as e:
        logger.error(f"Failed to update delivery status: {e}")


async def _process_template_updates(value: Dict[str, Any], field_type: str = None) -> None:
    """
    Process message template status updates.

    Args:
        value: Template update data
        field_type: Type of template update (message_template_status_update or message_template_quality_update)
    """
    logger.debug(f"Template update ({field_type}): {value}")
    # Handle template approval/rejection notifications
