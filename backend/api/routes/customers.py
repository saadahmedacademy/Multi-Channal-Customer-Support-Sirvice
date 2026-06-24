"""Customer lookup and management endpoints."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List
import logging

from backend.db.repositories.customer_repo import customer_repo, normalize_phone
from backend.db.repositories.customer_identifier_repo import customer_identifier_repo
from backend.db.repositories.conversation_repo import conversation_repo
from backend.api.schemas.messages import Channel
from backend.utils.auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["customers"])


@router.get("/lookup", dependencies=[Depends(get_api_key)])
async def lookup_customer(
    email: Optional[str] = Query(None, description="Customer email address"),
    phone: Optional[str] = Query(None, description="Customer phone number")
):
    """
    Lookup customer by email or phone.

    Used for cross-channel customer recognition.

    **Authentication**: Requires X-API-Key header

    **Input**: Email OR phone number

    **Returns**: Customer info with all linked identifiers
    """
    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided"
        )

    # Normalize phone if provided
    if phone:
        phone = normalize_phone(phone)

    # Try to find customer
    customer = None
    identifier_type = None

    if email:
        customer = await customer_repo.get_by_email(email)
        identifier_type = "email"
    
    if not customer and phone:
        customer = await customer_repo.get_by_phone(phone)
        identifier_type = "phone"

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Get all identifiers for this customer
    identifiers = await customer_identifier_repo.get_all_identifiers(customer.id)

    return {
        "customer": customer.to_dict(),
        "identifiers": identifiers,
        "lookup_type": identifier_type
    }


@router.get("/{customer_id}/conversations", dependencies=[Depends(get_api_key)])
async def get_customer_conversations(
    customer_id: str,
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return")
):
    """
    Get all conversations for a customer.

    **Input**: Customer UUID

    **Returns**: List of conversations with basic info
    """
    try:
        customer_uuid = UUID(customer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer ID format"
        )

    conversations = await conversation_repo.get_by_customer_id(customer_uuid, limit)

    return {
        "customer_id": customer_id,
        "conversations": [conv.to_dict() for conv in conversations],
        "total": len(conversations)
    }
