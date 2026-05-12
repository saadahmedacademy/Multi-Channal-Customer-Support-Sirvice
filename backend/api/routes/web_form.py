"""Web form submission endpoint."""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from uuid import UUID
import logging

from backend.api.schemas.tickets import (
    SupportFormSubmission,
    SupportFormResponse,
    ErrorResponse
)
from backend.api.schemas.messages import (
    MessageCreate,
    MessageRole,
    MessageDirection,
    Channel
)
from backend.db.repositories.customer_repo import customer_repo
from backend.db.repositories.conversation_repo import conversation_repo
from backend.db.repositories.ticket_repo import ticket_repo
from backend.db.connection import db
from backend.integrations.queue_client import queue_client, TOPICS
from backend.utils.security import (
    sanitize_name,
    sanitize_email,
    sanitize_phone,
    sanitize_subject,
    sanitize_customer_message
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["support"])


@router.post(
    "/submit",
    response_model=SupportFormResponse,
    responses={
        200: {"description": "Form submitted successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def submit_support_form(submission: SupportFormSubmission):
    """
    Submit a support request via web form.

    Creates a customer record, conversation, ticket, and queues the message
    for AI processing.

    **Input**: Support form data (name, email, subject, category, message)

    **Returns**: Ticket ID and confirmation message
    """
    try:
        # Step 0: Sanitize all user inputs to prevent XSS and injection attacks
        sanitized_name = sanitize_name(submission.name)
        sanitized_email = sanitize_email(submission.email)
        sanitized_phone = sanitize_phone(submission.phone) if submission.phone else None
        sanitized_subject = sanitize_subject(submission.subject)
        sanitized_message = sanitize_customer_message(submission.message)

        # Validate sanitized inputs
        if not sanitized_name or len(sanitized_name) < 2:
            raise ValueError("Invalid name provided")
        if not sanitized_email:
            raise ValueError("Invalid email address")
        if not sanitized_subject or len(sanitized_subject) < 5:
            raise ValueError("Invalid subject")
        if not sanitized_message or len(sanitized_message) < 10:
            raise ValueError("Invalid message content")

        # Step 1: Find or create customer
        customer = await customer_repo.find_or_create(
            email=sanitized_email,
            phone=sanitized_phone,
            name=sanitized_name
        )
        logger.info(f"Customer found/created: {customer.id}")

        # Step 2: Check for active conversation (within 24 hours)
        conversation = await conversation_repo.get_active_by_customer(
            customer_id=customer.id,
            hours=24
        )

        # Create new conversation if none exists
        if not conversation:
            conversation = await conversation_repo.create(
                customer_id=customer.id,
                initial_channel=Channel.WEB_FORM.value,
                metadata={
                    "subject": sanitized_subject,
                    "category": submission.category.value,
                    "priority": submission.priority.value
                }
            )
            logger.info(f"Conversation created: {conversation.id}")
        else:
            logger.info(f"Reusing existing conversation: {conversation.id}")

        # Step 3: Create ticket if conversation is new
        ticket = await ticket_repo.get_by_conversation_id(conversation.id)
        if not ticket:
            ticket = await ticket_repo.create(
                conversation_id=conversation.id,
                customer_id=customer.id,
                source_channel=Channel.WEB_FORM.value,
                category=submission.category.value,
                priority=submission.priority.value
            )
            logger.info(f"Ticket created: {ticket.id}")

        # Step 4: Create inbound message record
        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO messages
                    (conversation_id, channel, direction, role, content, delivery_status)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                conversation.id,
                Channel.WEB_FORM.value,
                MessageDirection.INBOUND.value,
                MessageRole.CUSTOMER.value,
                sanitized_message,
                "delivered"
            )

        # Step 5: Queue message for AI processing
        queue_message = {
            "type": "support_request",
            "ticket_id": str(ticket.id),
            "conversation_id": str(conversation.id),
            "customer_id": str(customer.id),
            "channel": Channel.WEB_FORM.value,
            "message": {
                "role": "customer",
                "content": sanitized_message,
                "subject": sanitized_subject,
                "category": submission.category.value,
                "priority": submission.priority.value
            },
            "customer": {
                "name": sanitized_name,
                "email": sanitized_email,
                "phone": sanitized_phone
            },
            "metadata": {
                "submission_time": datetime.utcnow().isoformat(),
                "priority": submission.priority.value,
                "category": submission.category.value
            }
        }

        await queue_client.publish(
            topic=TOPICS["tickets_incoming"],
            message=queue_message,
            key=str(ticket.id)
        )
        logger.info(f"Message queued for ticket {ticket.id}")

        # Step 6: Return success response
        return SupportFormResponse(
            ticket_id=f"TICKET-{str(ticket.id)[:8].upper()}",
            message="Thank you for contacting us! Our AI assistant will respond shortly.",
            estimated_response_time="Within 2 minutes",
            status=ticket.status
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting support form: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit support request"
        )
