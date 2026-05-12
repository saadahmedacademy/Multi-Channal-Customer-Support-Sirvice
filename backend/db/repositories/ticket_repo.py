"""Ticket repository for database operations."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from backend.db.models.ticket import Ticket
from backend.db.connection import db


class TicketRepository:
    """Repository for ticket database operations."""
    
    async def create(
        self,
        conversation_id: UUID,
        customer_id: UUID,
        source_channel: str,
        category: Optional[str] = None,
        priority: str = "medium"
    ) -> Ticket:
        """
        Create a new ticket.
        
        Args:
            conversation_id: Associated conversation ID
            customer_id: Customer ID
            source_channel: Channel where ticket originated
            category: Ticket category
            priority: Ticket priority
            
        Returns:
            Created Ticket instance
        """
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO tickets 
                    (conversation_id, customer_id, source_channel, category, priority)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, conversation_id, customer_id, source_channel, 
                          category, priority, status, created_at
            """, conversation_id, customer_id, source_channel, category, priority)
            
            return Ticket.from_row(row)
    
    async def get_by_id(self, ticket_id: UUID) -> Optional[Ticket]:
        """Get a ticket by ID."""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, conversation_id, customer_id, source_channel,
                       category, priority, status, created_at, resolved_at, resolution_notes
                FROM tickets
                WHERE id = $1
            """, ticket_id)
            
            return Ticket.from_row(row) if row else None
    
    async def get_by_conversation_id(
        self,
        conversation_id: UUID
    ) -> Optional[Ticket]:
        """Get a ticket by conversation ID."""
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, conversation_id, customer_id, source_channel,
                       category, priority, status, created_at, resolved_at, resolution_notes
                FROM tickets
                WHERE conversation_id = $1
            """, conversation_id)
            
            return Ticket.from_row(row) if row else None
    
    async def update_status(
        self,
        ticket_id: UUID,
        status: str,
        resolution_notes: Optional[str] = None,
        resolved_at: Optional[datetime] = None
    ) -> Optional[Ticket]:
        """
        Update ticket status.
        
        Args:
            ticket_id: Ticket ID to update
            status: New status
            resolution_notes: Notes about resolution
            resolved_at: When ticket was resolved
            
        Returns:
            Updated Ticket instance or None if not found
        """
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE tickets
                SET status = $1,
                    resolution_notes = COALESCE($2, resolution_notes),
                    resolved_at = COALESCE($3, resolved_at)
                WHERE id = $4
                RETURNING id, conversation_id, customer_id, source_channel,
                          category, priority, status, created_at, resolved_at, resolution_notes
            """, status, resolution_notes, resolved_at, ticket_id)
            
            return Ticket.from_row(row) if row else None
    
    async def get_by_customer_id(
        self,
        customer_id: UUID,
        limit: int = 20
    ) -> List[Ticket]:
        """Get tickets for a customer."""
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, conversation_id, customer_id, source_channel,
                       category, priority, status, created_at, resolved_at, resolution_notes
                FROM tickets
                WHERE customer_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, customer_id, limit)
            
            return [Ticket.from_row(row) for row in rows]
    
    async def get_by_status(
        self,
        status: str,
        limit: int = 50
    ) -> List[Ticket]:
        """Get tickets by status."""
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, conversation_id, customer_id, source_channel,
                       category, priority, status, created_at, resolved_at, resolution_notes
                FROM tickets
                WHERE status = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, status, limit)

            return [Ticket.from_row(row) for row in rows]

    async def get_all(self, limit: int = 100) -> List[Ticket]:
        """Get all tickets (limited)."""
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, conversation_id, customer_id, source_channel,
                       category, priority, status, created_at, resolved_at, resolution_notes
                FROM tickets
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)

            return [Ticket.from_row(row) for row in rows]


# Global repository instance
ticket_repo = TicketRepository()
