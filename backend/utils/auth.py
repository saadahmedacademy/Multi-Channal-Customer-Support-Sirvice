"""Authentication and authorization utilities."""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
import secrets
import hashlib
import hmac
import logging

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Returns:
        32-character hexadecimal API key
    """
    return secrets.token_hex(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.

    Args:
        api_key: Raw API key

    Returns:
        SHA-256 hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """
    Verify an API key against its stored hash.

    Args:
        provided_key: API key provided by client
        stored_hash: Stored hash of the valid API key

    Returns:
        True if key is valid
    """
    provided_hash = hash_api_key(provided_key)
    return hmac.compare_digest(provided_hash, stored_hash)


async def get_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    Dependency to validate API key from request header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Get valid API keys from settings
    valid_keys = _get_valid_api_keys()

    if not valid_keys:
        logger.error("No API keys configured in settings")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication not configured. Set INTERNAL_API_KEYS environment variable."
        )

    # Hash the incoming key for comparison
    provided_hash = hash_api_key(api_key)

    # Check if provided key matches any valid key
    for stored_key in valid_keys:
        # Support both SHA-256 hashed storage and plaintext (dev fallback)
        if len(stored_key) == 64 and all(c in '0123456789abcdef' for c in stored_key.lower()):
            if hmac.compare_digest(provided_hash, stored_key):
                logger.debug("API key validated successfully")
                return api_key
        else:
            if hmac.compare_digest(api_key, stored_key):
                logger.debug("API key validated successfully")
                return api_key

    logger.warning("Invalid API key attempt")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid API key"
    )


def _get_valid_api_keys() -> list[str]:
    """
    Get list of valid API keys from settings.

    Returns:
        List of valid API keys
    """
    # Support multiple API keys separated by commas
    api_keys_str = settings.internal_api_keys

    if not api_keys_str:
        return []

    # Split by comma and strip whitespace
    keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]

    return keys


async def get_optional_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[str]:
    """
    Optional API key dependency (doesn't raise error if missing).

    Useful for endpoints that have different behavior for authenticated vs
    unauthenticated requests.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        Validated API key or None
    """
    if not api_key:
        return None

    try:
        return await get_api_key(api_key)
    except HTTPException:
        return None
