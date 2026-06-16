"""Ticket status lookup endpoint."""

from fastapi import APIRouter, HTTPException, status
from uuid import UUID
import logging

from backend.api.schemas.tickets import (
    TicketStatusResponse,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    SurveyRating,
    SurveySubmitRequest,
    SurveyResponse,
    ErrorResponse
)
from backend.api.schemas.messages import (
    MessageSchema,
    MessageRole,
    MessageDirection,
    Channel,
    DeliveryStatus
)
from backend.db.repositories.ticket_repo import ticket_repo
from backend.db.repositories.conversation_repo import conversation_repo
from backend.db.repositories.survey_repo import survey_repo
from backend.db.connection import db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tickets"])


async def _resolve_ticket_id(ticket_id: str) -> UUID:
    """
    Parse ticket ID string to UUID.

    Accepts formats:
    - Full UUID: 550e8400-e29b-41d4-a716-446655440000
    - Short format: TICKET-550E8400 or 550E8400
    """
    clean_id = ticket_id.upper().replace("TICKET-", "")

    try:
        return UUID(ticket_id)
    except ValueError:
        try:
            return UUID(clean_id)
        except ValueError:
            if len(clean_id) == 8:
                tickets = await ticket_repo.get_all()
                for ticket in tickets:
                    if str(ticket.id).upper().startswith(clean_id):
                        return ticket.id
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticket not found: {ticket_id}"
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket not found: {ticket_id}"
            )


@router.get(
    "/ticket/{ticket_id}",
    response_model=TicketStatusResponse,
    responses={
        200: {"description": "Ticket found"},
        404: {"model": ErrorResponse, "description": "Ticket not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_ticket_status(ticket_id: str):
    """
    Get the status of a support ticket.

    **Input**: Ticket ID (UUID or TICKET-XXXXXX format)

    **Returns**: Ticket status with conversation messages
    """
    try:
        ticket_uuid = await _resolve_ticket_id(ticket_id)

        # Get ticket
        ticket = await ticket_repo.get_by_id(ticket_uuid)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket not found: {ticket_id}"
            )

        # Get conversation messages
        async with db.acquire() as conn:
            message_rows = await conn.fetch("""
                SELECT id, conversation_id, channel, direction, role, content,
                       created_at, tokens_used, latency_ms, delivery_status
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
            """, ticket.conversation_id)

        messages = []
        for row in message_rows:
            messages.append(MessageSchema(
                id=str(row["id"]),
                conversation_id=str(row["conversation_id"]),
                channel=Channel(row["channel"]),
                direction=MessageDirection(row["direction"]),
                role=MessageRole(row["role"]),
                content=row["content"],
                created_at=row["created_at"],
                tokens_used=row.get("tokens_used"),
                latency_ms=row.get("latency_ms"),
                delivery_status=DeliveryStatus(row["delivery_status"])
            ))

        # Get survey if ticket is resolved
        survey = None
        if ticket.status in ("resolved", "closed"):
            survey_data = await survey_repo.get_by_ticket_id(ticket_uuid)
            if survey_data:
                survey = SurveyResponse(
                    id=str(survey_data["id"]),
                    ticket_id=str(survey_data["ticket_id"]),
                    rating=SurveyRating(survey_data["rating"]),
                    reason=survey_data.get("reason"),
                    source=survey_data["source"],
                    created_at=survey_data["created_at"]
                )

        # Build response
        return TicketStatusResponse(
            ticket_id=f"TICKET-{str(ticket.id)[:8].upper()}",
            status=TicketStatus(ticket.status),
            category=TicketCategory(ticket.category) if ticket.category else None,
            priority=TicketPriority(ticket.priority),
            created_at=ticket.created_at,
            resolved_at=ticket.resolved_at,
            messages=messages,
            resolution_notes=ticket.resolution_notes,
            survey=survey
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticket status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket status"
        )


@router.post(
    "/ticket/{ticket_id}/survey",
    response_model=SurveyResponse,
    responses={
        200: {"description": "Survey submitted"},
        404: {"model": ErrorResponse, "description": "Ticket not found"},
        400: {"model": ErrorResponse, "description": "Ticket not resolved"}
    }
)
async def submit_survey(ticket_id: str, survey_data: SurveySubmitRequest):
    """
    Submit a survey response for a resolved ticket.

    **Input**: Ticket ID + rating (thumbs_up/thumbs_down) + optional reason

    **Returns**: Saved survey data
    """
    try:
        ticket_uuid = await _resolve_ticket_id(ticket_id)
        ticket = await ticket_repo.get_by_id(ticket_uuid)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket not found: {ticket_id}"
            )

        if ticket.status not in ("resolved", "closed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Survey is only available for resolved tickets"
            )

        result = await survey_repo.save_survey(
            ticket_id=ticket_uuid,
            rating=survey_data.rating.value,
            reason=survey_data.reason,
            source="api"
        )

        return SurveyResponse(
            id=str(result["id"]),
            ticket_id=str(result["ticket_id"]),
            rating=SurveyRating(result["rating"]),
            reason=result.get("reason"),
            source=result["source"],
            created_at=result["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting survey: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit survey"
        )
