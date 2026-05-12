"""Conversation history and management endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from uuid import UUID
import logging

from backend.db.repositories.conversation_repo import conversation_repo
from backend.db.connection import db
from backend.api.schemas.messages import MessageSchema, MessageRole, MessageDirection, Channel, DeliveryStatus
from backend.utils.auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


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
