"""Email webhook endpoints for receiving emails and status updates."""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
import logging
import base64
import re
import email
from email.header import decode_header
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.config.settings import settings
from backend.integrations.queue_client import queue_client, TOPICS
from backend.db.connection import db
from backend.integrations.email_client import gmail_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])


def decode_mime_words(text: str) -> str:
    """
    Decode MIME encoded words in email headers.

    Args:
        text: Header text with possible MIME encoding

    Returns:
        Decoded UTF-8 string
    """
    if not text:
        return ""

    decoded_parts = []
    for part, encoding in decode_header(text):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or 'utf-8'))
            except (UnicodeDecodeError, LookupError):
                decoded_parts.append(part.decode('latin-1'))
        else:
            decoded_parts.append(part)

    return "".join(decoded_parts)


def parse_email_content(raw_email: str) -> Dict[str, Any]:
    """
    Parse raw email content.

    Args:
        raw_email: Raw email string

    Returns:
        Parsed email data
    """
    msg = email.message_from_string(raw_email)

    # Extract headers
    subject = decode_mime_words(msg.get("Subject", ""))
    from_header = decode_mime_words(msg.get("From", ""))
    to_header = decode_mime_words(msg.get("To", ""))
    date_header = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")
    in_reply_to = msg.get("In-Reply-To", "")
    references = msg.get("References", "")

    # Parse From header to extract email address
    from_email = from_header
    if "<" in from_header and ">" in from_header:
        from_email = from_header.split("<")[1].split(">")[0].strip()

    # Get email body
    body = ""
    html_body = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get_content_disposition() or "")

            # Skip attachments
            if "attachment" in content_disposition:
                filename = part.get_filename()
                if filename:
                    attachments.append({
                        "filename": decode_mime_words(filename),
                        "content_type": content_type
                    })
                continue

            # Get text parts
            try:
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Failed to decode email part: {e}")
    else:
        # Single part email
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Failed to decode email body: {e}")

    # Use HTML body if plain text is empty
    if not body and html_body:
        # Strip HTML tags for plain text version
        body = re.sub(r'<[^>]+>', '', html_body)

    return {
        "subject": subject,
        "from": from_header,
        "from_email": from_email,
        "to": to_header,
        "date": date_header,
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references,
        "body": body,
        "html_body": html_body,
        "attachments": attachments,
        "is_reply": bool(in_reply_to or (subject.lower().startswith("re:")))
    }


@router.post("/email")
async def email_webhook_receive(request: Request):
    """
    Email webhook for receiving emails.

    Accepts emails forwarded from Gmail via Pub/Sub or webhook.

    Expected payload format (Gmail Pub/Sub):
    {
        "message": {
            "data": "<base64-encoded-email>",
            "messageId": "<gmail-message-id>",
            "attributes": {}
        },
        "subscription": "<subscription-name>"
    }
    """
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse email webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )

    logger.debug(f"Email webhook received: {data}")

    # Handle Gmail Pub/Sub format
    if "message" in data and "data" in data["message"]:
        try:
            # Decode base64 email
            email_data = base64.urlsafe_b64decode(data["message"]["data"]).decode('utf-8')
            gmail_message_id = data["message"].get("messageId", "")

            # Parse email content
            parsed_email = parse_email_content(email_data)

            # Process the email
            await _handle_incoming_email(
                email_data=parsed_email,
                message_id=gmail_message_id,
                raw_email=email_data
            )

        except Exception as e:
            logger.error(f"Failed to process Gmail message: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": str(e)}
            )

    # Handle simple email format (for testing/custom integrations)
    elif "from_email" in data or "from" in data:
        parsed_email = {
            "subject": data.get("subject", "No Subject"),
            "from": data.get("from", data.get("from_email", "")),
            "from_email": data.get("from_email", ""),
            "to": data.get("to", ""),
            "body": data.get("body", ""),
            "html_body": data.get("html_body", ""),
            "message_id": data.get("message_id", ""),
            "in_reply_to": data.get("in_reply_to", ""),
            "is_reply": data.get("is_reply", False),
            "attachments": data.get("attachments", [])
        }

        await _handle_incoming_email(
            email_data=parsed_email,
            message_id=data.get("message_id", ""),
            raw_email=""
        )

    else:
        logger.warning(f"Unknown email format: {data}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown email format"
        )

    return JSONResponse(content={"status": "received"})


async def _handle_incoming_email(
    email_data: Dict[str, Any],
    message_id: str,
    raw_email: str = ""
) -> None:
    """
    Handle incoming email message.

    Args:
        email_data: Parsed email data
        message_id: Gmail message ID
        raw_email: Raw email string
    """
    from_email = email_data.get("from_email", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")
    is_reply = email_data.get("is_reply", False)
    attachments = email_data.get("attachments", [])

    logger.info(f"Received email from {from_email}: {subject}")

    # Handle attachments
    if attachments:
        attachment_summary = f"[{len(attachments)} attachment(s): {', '.join([a['filename'] for a in attachments])}]"
        body = f"{body}\n\n{attachment_summary}"
        logger.info(f"Email has attachments: {[a['filename'] for a in attachments]}")

    # Extract customer email (remove name if present)
    if "<" in from_email and ">" in from_email:
        from_email = from_email.split("<")[1].split(">")[0].strip()

    # Create customer message payload
    customer_message = {
        "type": "email_message",
        "channel": "email",
        "from_email": from_email,
        "from_name": email_data.get("from", "").split("<")[0].strip() if "<" in email_data.get("from", "") else "",
        "message_id": message_id,
        "timestamp": datetime.utcnow().isoformat(),
        "content": body,
        "subject": subject,
        "is_reply": is_reply,
        "in_reply_to": email_data.get("in_reply_to", ""),
        "references": email_data.get("references", ""),
        "html_body": email_data.get("html_body", ""),
        "raw_email": raw_email
    }

    # Queue for processing
    try:
        await queue_client.publish(
            topic=TOPICS["tickets_incoming"],
            message=customer_message,
            key=from_email
        )
        logger.info(f"Email message queued: {message_id}")
    except Exception as e:
        logger.error(f"Failed to queue email message: {e}")


@router.get("/email/test")
async def test_email_webhook():
    """
    Test email webhook endpoint.

    Returns a simple response to verify the endpoint is working.
    """
    return {
        "status": "ok",
        "message": "Email webhook endpoint is running",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/email/gmail/sync")
async def sync_gmail_emails(request: Request):
    """
    Manually trigger Gmail email sync.

    This endpoint fetches unread emails from Gmail and queues them for processing.
    Useful for testing or manual sync when not using Pub/Sub.

    Query params:
        max_results: Maximum number of emails to fetch (default: 10)
    """
    query_params = request.query_params
    max_results = int(query_params.get("max_results", 10))

    if not gmail_client.is_configured():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Gmail client not configured"}
        )

    try:
        # Fetch unread emails from support inbox
        result = await gmail_client.list_messages(
            query=f"from:not(me) is:unread to:{gmail_client.support_email}",
            max_results=max_results
        )

        if "error" in result:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": result["error"]}
            )

        messages = result.get("messages", [])
        processed_count = 0

        for msg_summary in messages:
            message_id = msg_summary.get("id")
            if not message_id:
                continue

            # Get full message
            msg_data = await gmail_client.get_message(message_id, format="full")

            if "error" in msg_data:
                logger.warning(f"Failed to get message {message_id}: {msg_data['error']}")
                continue

            # Parse message data
            payload = msg_data.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

            subject = headers.get("Subject", "")
            from_header = headers.get("From", "")
            date = headers.get("Date", "")
            in_reply_to = headers.get("In-Reply-To", "")

            # Extract from email
            from_email = from_header
            if "<" in from_header and ">" in from_header:
                from_email = from_header.split("<")[1].split(">")[0].strip()

            # Get body
            body = ""
            html_body = ""

            # Try to get body from parts
            def extract_body(part):
                nonlocal body, html_body
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode('utf-8')
                elif part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                    html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode('utf-8')
                elif "parts" in part:
                    for subpart in part["parts"]:
                        extract_body(subpart)

            extract_body(payload)

            # Create email payload
            email_payload = {
                "type": "email_message",
                "channel": "email",
                "from_email": from_email,
                "from_name": from_header.split("<")[0].strip() if "<" in from_header else "",
                "message_id": message_id,
                "timestamp": date,
                "content": body or html_body,
                "subject": subject,
                "is_reply": bool(in_reply_to),
                "in_reply_to": in_reply_to,
                "html_body": html_body
            }

            # Queue for processing
            await queue_client.publish(
                topic=TOPICS["tickets_incoming"],
                message=email_payload,
                key=from_email
            )

            # Mark as read in Gmail
            await gmail_client.mark_as_read(message_id)

            processed_count += 1
            logger.info(f"Processed email {message_id} from {from_email}")

        return {
            "status": "success",
            "processed_count": processed_count,
            "total_found": len(messages),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to sync Gmail emails: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )
