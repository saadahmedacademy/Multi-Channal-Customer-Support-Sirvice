"""Link customer identifiers endpoint."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from backend.db.repositories.customer_repo import customer_repo, normalize_phone
from backend.db.repositories.customer_identifier_repo import customer_identifier_repo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["customers"])


class LinkIdentifierRequest(BaseModel):
    """Request to link two identifiers."""
    email: Optional[str] = None
    phone: Optional[str] = None
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None


class LinkIdentifierResponse(BaseModel):
    """Response after linking identifiers."""
    customer_id: str
    message: str
    identifiers: list


@router.post("/link-identifiers", response_model=LinkIdentifierResponse)
async def link_customer_identifiers(request: LinkIdentifierRequest):
    """
    Link customer identifiers (email and phone) to unify their profile.

    This enables cross-channel continuity by recognizing the same customer
    across different channels (web form, WhatsApp, email).

    **Use Cases**:
    - Customer provides email on web form, then contacts via WhatsApp with phone
    - System links both identifiers to same customer profile
    - Conversation history becomes unified across channels

    **Input**:
    - email: Email address to link
    - phone: Phone number to link
    - primary_email: Existing primary email (if known)
    - primary_phone: Existing primary phone (if known)

    **Returns**:
    - customer_id: Unified customer ID
    - identifiers: All linked identifiers
    """
    try:
        # Validate input
        if not request.email and not request.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one identifier (email or phone) must be provided"
            )

        # Normalize phone if provided
        phone_to_use = None
        if request.phone:
            phone_to_use = normalize_phone(request.phone)

        # Step 1: Find existing customers
        email_customer = None
        phone_customer = None

        if request.email:
            email_customer = await customer_repo.get_by_email(request.email)

        if phone_to_use:
            phone_customer = await customer_repo.get_by_phone(phone_to_use)

        # Step 2: Determine primary customer
        primary_customer = None

        # If both exist and are different, we need to merge
        if email_customer and phone_customer and email_customer.id != phone_customer.id:
            # Merge phone_customer into email_customer (prefer email as primary)
            primary_customer = email_customer

            # Link phone_customer's identifiers to email_customer
            phone_identifiers = await customer_identifier_repo.get_all_identifiers(phone_customer.id)
            for identifier in phone_identifiers:
                await customer_identifier_repo.add_identifier(
                    customer_id=primary_customer.id,
                    identifier_type=identifier["identifier_type"],
                    identifier_value=identifier["identifier_value"],
                    verified=identifier["verified"]
                )

            # Add the new phone number
            await customer_identifier_repo.add_identifier(
                customer_id=primary_customer.id,
                identifier_type="phone",
                identifier_value=phone_to_use,
                verified=True
            )

            # Update email_customer's phone if empty
            if not primary_customer.phone:
                await customer_repo.update(
                    customer_id=primary_customer.id,
                    phone=phone_to_use
                )

            logger.info(f"Merged customer {phone_customer.id} into {primary_customer.id}")

        elif email_customer:
            primary_customer = email_customer

            # Add phone identifier if not exists
            if phone_to_use:
                await customer_identifier_repo.add_identifier(
                    customer_id=primary_customer.id,
                    identifier_type="phone",
                    identifier_value=phone_to_use,
                    verified=True
                )

                # Update customer phone if empty
                if not primary_customer.phone:
                    await customer_repo.update(
                        customer_id=primary_customer.id,
                        phone=phone_to_use
                    )

        elif phone_customer:
            primary_customer = phone_customer

            # Add email identifier if not exists
            if request.email:
                await customer_identifier_repo.add_identifier(
                    customer_id=primary_customer.id,
                    identifier_type="email",
                    identifier_value=request.email,
                    verified=True
                )

                # Update customer email if empty
                if not primary_customer.email:
                    await customer_repo.update(
                        customer_id=primary_customer.id,
                        email=request.email
                    )

        else:
            # Create new customer
            name = request.primary_email or request.primary_phone or "Unknown"
            primary_customer = await customer_repo.find_or_create(
                email=request.email,
                phone=phone_to_use,
                name=name
            )

        # Step 3: Ensure both identifiers are linked
        if request.email:
            await customer_identifier_repo.add_identifier(
                customer_id=primary_customer.id,
                identifier_type="email",
                identifier_value=request.email,
                verified=True
            )

        if phone_to_use:
            await customer_identifier_repo.add_identifier(
                customer_id=primary_customer.id,
                identifier_type="phone",
                identifier_value=phone_to_use,
                verified=True
            )

        # Step 4: Get all identifiers
        identifiers = await customer_identifier_repo.get_all_identifiers(primary_customer.id)

        return LinkIdentifierResponse(
            customer_id=str(primary_customer.id),
            message="Customer identifiers linked successfully",
            identifiers=identifiers
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking identifiers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link customer identifiers"
        )


@router.get("/{customer_id}/identifiers")
async def get_customer_identifiers(customer_id: str):
    """
    Get all identifiers linked to a customer.

    **Input**: Customer UUID

    **Returns**: List of all identifiers (emails, phones, etc.)
    """
    try:
        customer_uuid = UUID(customer_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid customer ID format"
        )

    identifiers = await customer_identifier_repo.get_all_identifiers(customer_uuid)

    return {
        "customer_id": customer_id,
        "identifiers": identifiers,
        "total": len(identifiers)
    }
