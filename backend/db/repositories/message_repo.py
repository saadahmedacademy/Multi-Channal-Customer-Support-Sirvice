"""Message repository for database operations."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from backend.db.connection import db


class MessageRepository:
    """Repository for message database operations."""

    async def get_by_conversation(self, conversation_id: UUID) -> List[Dict[str, Any]]:
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, conversation_id, channel, direction, role, content,
                       created_at, tokens_used, latency_ms, delivery_status,
                       feedback, feedback_reason, feedback_created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
            """, conversation_id)
            return [dict(r) for r in rows]

    async def set_feedback(
        self,
        message_id: UUID,
        rating: str,
        reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE messages
                SET feedback = $1,
                    feedback_reason = $2,
                    feedback_created_at = NOW()
                WHERE id = $3
                RETURNING id, feedback, feedback_reason, feedback_created_at
            """, rating, reason, message_id)
            return dict(row) if row else None

    async def get_latest_agent_message(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, conversation_id, channel, direction, role, content,
                       created_at, tokens_used, latency_ms, delivery_status,
                       feedback, feedback_reason, feedback_created_at
                FROM messages
                WHERE conversation_id = $1 AND role = 'agent' AND direction = 'outbound'
                ORDER BY created_at DESC
                LIMIT 1
            """, conversation_id)
            return dict(row) if row else None


message_repo = MessageRepository()
