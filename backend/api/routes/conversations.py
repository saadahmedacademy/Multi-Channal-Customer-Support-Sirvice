"""Conversation history and management endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID
import logging

from backend.db.repositories.conversation_repo import conversation_repo
from backend.db.repositories.message_repo import message_repo
from backend.db.repositories.ticket_repo import ticket_repo
from backend.db.connection import db
from backend.api.schemas.messages import (
    MessageSchema, MessageRole, MessageDirection, Channel, DeliveryStatus,
    FeedbackRating, FeedbackSubmit, FollowUpMessage, FollowUpResponse
)
from backend.utils.auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])


@router.get("/{conversation_id}", dependencies=[Depends(get_api_key)])
async def get_conversation(conversation_id: str):
    """
    Get conversation details with all messages.

    **Authentication**: Requires X-API-Key header

    **Input**: Conversation UUID

    **Returns**: Conversation with full message history
    """
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format"
        )

    # Get conversation
    conversation = await conversation_repo.get_by_id(conv_uuid)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get messages
    async with db.acquire() as conn:
        message_rows = await conn.fetch("""
            SELECT id, conversation_id, channel, direction, role, content,
                   created_at, tokens_used, latency_ms, delivery_status
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """, conv_uuid)

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

    return {
        "conversation": conversation.to_dict(),
        "messages": [msg.dict() for msg in messages],
        "message_count": len(messages)
    }


@router.get("/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    limit: int = 50
):
    """
    Get conversation history (last N messages).

    **Input**: Conversation UUID, optional limit

    **Returns**: Last N messages in chronological order
    """
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format"
        )

    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, conversation_id, channel, direction, role, content,
                   created_at, tokens_used, latency_ms, delivery_status
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, conv_uuid, limit)

    messages = []
    for row in reversed(rows):  # Reverse to get chronological order
        messages.append({
            "id": str(row["id"]),
            "conversation_id": str(row["conversation_id"]),
            "channel": row["channel"],
            "direction": row["direction"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"],
            "tokens_used": row.get("tokens_used"),
            "latency_ms": row.get("latency_ms"),
            "delivery_status": row.get("delivery_status")
        })

    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "count": len(messages)
    }


@router.post("/{conversation_id}/messages")
async def send_follow_up(conversation_id: str, body: FollowUpMessage):
    """
    Send a follow-up message in an existing conversation and get AI response.

    **Input**: Conversation ID + message content

    **Returns**: AI response with message IDs
    """
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format"
        )

    conversation = await conversation_repo.get_by_id(conv_uuid)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    ticket = await ticket_repo.get_by_conversation_id(conv_uuid)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ticket found for this conversation"
        )

    # Enforce 7-message session limit (count only customer + agent messages)
    async with db.acquire() as conn:
        msg_count = await conn.fetchval("""
            SELECT COUNT(*) FROM messages
            WHERE conversation_id = $1 AND role IN ('customer', 'agent')
        """, conv_uuid)

    if msg_count is not None and msg_count >= 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This conversation session has ended. For further assistance, please create a new support ticket."
        )

    # Save customer message
    async with db.acquire() as conn:
        msg_row = await conn.fetchrow("""
            INSERT INTO messages (conversation_id, channel, direction, role, content, delivery_status)
            VALUES ($1, 'web_form', 'inbound', 'customer', $2, 'delivered')
            RETURNING id, created_at
        """, conv_uuid, body.content)

    # Get conversation history
    history_rows = await message_repo.get_by_conversation(conv_uuid)
    conv_history = [
        {"role": r["role"], "content": r["content"]}
        for r in history_rows if r["role"] in ("customer", "agent")
    ]

    # Generate AI response
    from backend.worker.ai_agent import ai_agent
    from backend.worker.sentiment import sentiment_analyzer

    sentiment_result = sentiment_analyzer.analyze(body.content)
    response_text, tokens_used, confidence = await ai_agent.generate_response(
        message=body.content,
        channel="web_form",
        conversation_history=conv_history,
        knowledge_context=[],
        customer_metadata={}
    )

    # Save AI response
    async with db.acquire() as conn:
        resp_row = await conn.fetchrow("""
            INSERT INTO messages (conversation_id, channel, direction, role, content,
                                  tokens_used, delivery_status)
            VALUES ($1, 'web_form', 'outbound', 'agent', $2, $3, 'sent')
            RETURNING id, created_at
        """, conv_uuid, response_text, tokens_used)

    # Update ticket status
    await ticket_repo.update_status(
        ticket_id=ticket.id,
        status="in_progress",
        resolution_notes=f"AI responded with {tokens_used} tokens"
    )

    return FollowUpResponse(
        message_id=str(msg_row["id"]),
        response_message_id=str(resp_row["id"]),
        response=response_text,
        tokens_used=tokens_used,
        created_at=resp_row["created_at"]
    )


@router.post("/messages/{message_id}/feedback")
async def submit_feedback(message_id: str, body: FeedbackSubmit):
    """
    Submit thumbs up/down feedback for a specific message.

    **Input**: Message ID + rating + optional reason

    **Returns**: Updated feedback status
    """
    try:
        msg_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID format"
        )

    result = await message_repo.set_feedback(
        message_id=msg_uuid,
        rating=body.rating.value,
        reason=body.reason
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    return {
        "message_id": message_id,
        "feedback": result["feedback"],
        "feedback_reason": result.get("feedback_reason"),
        "feedback_created_at": result["feedback_created_at"].isoformat() if result.get("feedback_created_at") else None
    }
