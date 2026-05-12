#!/usr/bin/env python3
"""
Simple Gmail email fetcher for support tickets.

This script periodically checks Gmail for unread support emails
and forwards them to your AI Support Agent webhook.

Usage:
    python scripts/fetch_gmail_emails.py
"""

import httpx
import time
import base64
import logging
from datetime import datetime, timedelta
from email.header import decode_header
import email
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

load_dotenv()

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhooks/email"
POLL_INTERVAL = 60  # Check every 60 seconds
MAX_RESULTS = 10    # Process up to 10 emails per poll

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_valid_token():
    """Retrieve and refresh the Google OAuth token if necessary."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open('token.json', 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return None
        else:
            logger.error("No valid token.json found or refresh token is missing. Please run 'python scripts/get_gmail_token.py' first.")
            return None
    
    return creds.token


def decode_mime_words(text):
    """Decode MIME encoded words."""
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


def parse_email(raw_email_bytes):
    """Parse raw email content."""
    msg = email.message_from_bytes(raw_email_bytes)
    
    subject = decode_mime_words(msg.get("Subject", ""))
    from_header = decode_mime_words(msg.get("From", ""))
    date_header = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")
    in_reply_to = msg.get("In-Reply-To", "")
    
    # Extract email address
    from_email = from_header
    if "<" in from_header and ">" in from_header:
        from_email = from_header.split("<")[1].split(">")[0].strip()
    
    # Get body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                if "attachment" not in str(part.get_content_disposition() or ""):
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    
    return {
        "subject": subject,
        "from": from_header,
        "from_email": from_email,
        "date": date_header,
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "body": body
    }


def fetch_unread_emails(token):
    """Fetch unread emails from Gmail."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    # List unread messages
    response = httpx.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers=headers,
        params={
            "q": "is:unread",
            "maxResults": MAX_RESULTS
        }
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to list messages: {response.text}")
        return []
    
    messages = response.json().get("messages", [])
    logger.info(f"Found {len(messages)} unread emails")
    
    emails = []
    for msg in messages:
        msg_id = msg["id"]
        
        # Get full message
        msg_response = httpx.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
            headers=headers,
            params={"format": "raw"}
        )
        
        if msg_response.status_code == 200:
            raw_email = base64.urlsafe_b64decode(msg_response.json()["raw"])
            parsed = parse_email(raw_email)
            parsed["gmail_id"] = msg_id
            emails.append(parsed)
    
    return emails


def mark_as_read(token, message_id):
    """Mark email as read."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = httpx.post(
        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify",
        headers=headers,
        json={"removeLabelIds": ["UNREAD"]}
    )
    
    return response.status_code == 200


def forward_to_webhook(email_data):
    """Forward email to AI Support Agent webhook."""
    payload = {
        "from_email": email_data["from_email"],
        "from": email_data["from"],
        "subject": email_data["subject"],
        "body": email_data["body"],
        "message_id": email_data.get("gmail_id", ""),
        "in_reply_to": email_data.get("in_reply_to", ""),
        "is_reply": bool(email_data.get("in_reply_to"))
    }
    
    try:
        response = httpx.post(WEBHOOK_URL, json=payload, timeout=30.0)
        
        if response.status_code == 200:
            logger.info(f"✓ Forwarded: {email_data['subject']} from {email_data['from_email']}")
            return True
        else:
            logger.error(f"✗ Webhook returned {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Failed to forward email: {e}")
        return False


def main():
    """Main polling loop."""
    logger.info("Starting Gmail email fetcher...")
    logger.info(f"Webhook URL: {WEBHOOK_URL}")
    logger.info(f"Poll interval: {POLL_INTERVAL} seconds")
    
    while True:
        try:
            # Refresh token if needed
            current_token = get_valid_token()
            if not current_token:
                logger.info("Sleeping before retry...")
                time.sleep(POLL_INTERVAL)
                continue
                
            # Fetch unread emails
            unread_emails = fetch_unread_emails(current_token)
            
            # Process each email
            for email_data in unread_emails:
                logger.info(f"Processing: {email_data['subject']} from {email_data['from_email']}")
                
                # Forward to webhook
                success = forward_to_webhook(email_data)
                
                # Mark as read if successfully forwarded
                if success:
                    mark_as_read(current_token, email_data["gmail_id"])
                    logger.info(f"✓ Marked as read: {email_data['gmail_id']}")
            
            # Wait for next poll
            logger.info(f"Sleeping for {POLL_INTERVAL} seconds...")
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
            time.sleep(30)  # Wait before retry


if __name__ == "__main__":
    main()
