"""Conversation repository for database operations."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import json
from backend.db.models.conversation import Conversation
from backend.db.connection import db


class ConversationRepository:
    """Repository for conversation database operations."""
    
    async def create(
        self,
        customer_id: UUID,
        initial_channel: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            customer_id: Customer ID
            initial_channel: Channel where conversation started
            metadata: Additional conversation attributes
            
        Returns:
            Created Conversation instance
        """
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO conversations (customer_id, initial_channel, metadata)
                VALUES ($1, $2, $3)
                RETURNING id, customer_id, initial_channel, started_at, status, metadata
            """, customer_id, initial_channel, json.dumps(metadata or {}))

            return Conversation.from_row(row)
    
    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, customer_id, initial_channel, started_at, ended_at,
                       status, sentiment_score, resolution_type, escalated_to, metadata
                FROM conversations
                WHERE id = $1
            """, conversation_id)
            
            return Conversation.from_row(row) if row else None
    
    async def get_active_by_customer(
        self,
        customer_id: UUID,
        hours: int = 24
    ) -> Optional[Conversation]:
        """
        Get active conversation for a customer within time window.
        
        Args:
            customer_id: Customer ID
            hours: Look back period in hours (default 24)
            
        Returns:
            Active Conversation or None
        """
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, customer_id, initial_channel, started_at, ended_at,
                       status, sentiment_score, resolution_type, escalated_to, metadata
                FROM conversations
                WHERE customer_id = $1
                  AND status = 'active'
                  AND started_at > NOW() - ($2 * INTERVAL '1 hour')
                ORDER BY started_at DESC
                LIMIT 1
            """, customer_id, hours)
            
            return Conversation.from_row(row) if row else None
    
    async def update_status(
        self,
        conversation_id: UUID,
        status: str,
        ended_at: Optional[datetime] = None
    ) -> Optional[Conversation]:
        """
        Update conversation status.
        
        Args:
            conversation_id: Conversation ID
            status: New status
            ended_at: When conversation ended
            
        Returns:
            Updated Conversation or None if not found
        """
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE conversations
                SET status = $1,
                    ended_at = COALESCE($2, ended_at)
                WHERE id = $3
                RETURNING id, customer_id, initial_channel, started_at, 
                          ended_at, status, metadata
            """, status, ended_at, conversation_id)
            
            return Conversation.from_row(row) if row else None
    
    async def update_sentiment(
        self,
        conversation_id: UUID,
        sentiment_score: Decimal
    ) -> Optional[Conversation]:
        """Update conversation sentiment score."""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE conversations
                SET sentiment_score = $1
                WHERE id = $2
                RETURNING id, customer_id, initial_channel, started_at,
                          ended_at, status, sentiment_score, metadata
            """, sentiment_score, conversation_id)
            
            return Conversation.from_row(row) if row else None
    
    async def get_by_customer_id(
        self,
        customer_id: UUID,
        limit: int = 20
    ) -> List[Conversation]:
        """Get conversations for a customer."""
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, customer_id, initial_channel, started_at, ended_at,
                       status, sentiment_score, resolution_type, escalated_to, metadata
                FROM conversations
                WHERE customer_id = $1
                ORDER BY started_at DESC
                LIMIT $2
            """, customer_id, limit)

            return [Conversation.from_row(row) for row in rows]

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get recent messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dicts with role and content in chronological order
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT role, content
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, conversation_id, limit)

            # Reverse to get chronological order (oldest first)
            return [
                {"role": row["role"], "content": row["content"]}
                for row in reversed(rows)
            ]


# Global repository instance
conversation_repo = ConversationRepository()
