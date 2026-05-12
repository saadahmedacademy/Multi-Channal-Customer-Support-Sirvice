"""Security utilities for input sanitization and validation."""

import bleach
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# Allowed HTML tags for email content (safe subset)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre',
    'span', 'div', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'span': ['style'],
    'div': ['style'],
    'p': ['style'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan']
}

# Allowed CSS properties (for style attributes)
ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-weight',
    'text-align', 'padding', 'margin', 'border'
]


def sanitize_html(html_content: str, strip: bool = False) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        html_content: Raw HTML content
        strip: If True, strip all HTML tags. If False, allow safe tags.

    Returns:
        Sanitized HTML content
    """
    if not html_content:
        return ""

    if strip:
        # Strip all HTML tags, leaving only text
        return bleach.clean(html_content, tags=[], strip=True)

    # Allow safe HTML tags and attributes
    # Note: bleach 6.x removed the 'styles' parameter
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

    return cleaned


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize plain text input by removing potentially dangerous characters.

    Args:
        text: Raw text input
        max_length: Optional maximum length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove control characters except newlines, tabs, and carriage returns
    text = re.sub(r'[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Normalize whitespace (collapse multiple spaces)
    text = re.sub(r'\s+', ' ', text)

    # Trim whitespace
    text = text.strip()

    # Apply max length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def sanitize_email(email: str) -> str:
    """
    Sanitize email address.

    Args:
        email: Raw email address

    Returns:
        Sanitized email address
    """
    if not email:
        return ""

    # Remove whitespace
    email = email.strip().lower()

    # Basic validation pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        logger.warning(f"Invalid email format: {email}")
        return ""

    return email


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number.

    Args:
        phone: Raw phone number

    Returns:
        Sanitized phone number (digits and + only)
    """
    if not phone:
        return ""

    # Keep only digits, +, and spaces
    phone = re.sub(r'[^0-9+\s-]', '', phone)

    # Remove extra whitespace
    phone = phone.strip()

    return phone


def sanitize_url(url: str) -> str:
    """
    Sanitize URL to prevent javascript: and data: schemes.

    Args:
        url: Raw URL

    Returns:
        Sanitized URL or empty string if dangerous
    """
    if not url:
        return ""

    url = url.strip().lower()

    # Block dangerous schemes
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
    for scheme in dangerous_schemes:
        if url.startswith(scheme):
            logger.warning(f"Blocked dangerous URL scheme: {url}")
            return ""

    # Only allow http, https, mailto
    if not (url.startswith('http://') or url.startswith('https://') or url.startswith('mailto:')):
        # If no scheme, assume https
        url = 'https://' + url

    return url


def sanitize_customer_message(
    content: str,
    max_length: int = 10000
) -> str:
    """
    Sanitize customer message content.

    Args:
        content: Raw message content
        max_length: Maximum allowed length

    Returns:
        Sanitized message content
    """
    # Strip any HTML tags (customers shouldn't send HTML)
    content = sanitize_html(content, strip=True)

    # Sanitize as text
    content = sanitize_text(content, max_length=max_length)

    return content


def sanitize_subject(subject: str, max_length: int = 500) -> str:
    """
    Sanitize email/ticket subject line.

    Args:
        subject: Raw subject
        max_length: Maximum allowed length

    Returns:
        Sanitized subject
    """
    # Strip HTML
    subject = sanitize_html(subject, strip=True)

    # Sanitize as text
    subject = sanitize_text(subject, max_length=max_length)

    return subject


def sanitize_name(name: str, max_length: int = 255) -> str:
    """
    Sanitize customer name.

    Args:
        name: Raw name
        max_length: Maximum allowed length

    Returns:
        Sanitized name
    """
    # Strip HTML
    name = sanitize_html(name, strip=True)

    # Sanitize as text
    name = sanitize_text(name, max_length=max_length)

    # Remove special characters except spaces, hyphens, apostrophes
    name = re.sub(r"[^a-zA-Z0-9\s\-'.]", '', name)

    return name.strip()
