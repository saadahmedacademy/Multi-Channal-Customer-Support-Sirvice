"""Ticket service for ticket lifecycle management."""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from backend.db.repositories.ticket_repo import ticket_repo
from backend.db.repositories.conversation_repo import conversation_repo
from backend.db.connection import db

logger = logging.getLogger(__name__)


class TicketService:
    """Service for managing ticket lifecycle."""

    async def create_ticket(
        self,
        conversation_id: UUID,
        customer_id: UUID,
        source_channel: str,
        category: Optional[str] = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create a new ticket.

        Args:
            conversation_id: Associated conversation ID
            customer_id: Customer ID
            source_channel: Channel where ticket originated
            category: Ticket category
            priority: Ticket priority

        Returns:
            Ticket data as dictionary
        """
        ticket = await ticket_repo.create(
            conversation_id=conversation_id,
            customer_id=customer_id,
            source_channel=source_channel,
            category=category,
            priority=priority
        )

        logger.info(f"Ticket created: {ticket.id} for customer {customer_id}")

        return ticket.to_dict()

    async def update_ticket_status(
        self,
        ticket_id: UUID,
        status: str,
        resolution_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update ticket status.

        Args:
            ticket_id: Ticket ID to update
            status: New status
            resolution_notes: Notes about resolution

        Returns:
            Updated ticket data or None if not found
        """
        resolved_at = None
        if status in ["resolved", "closed"]:
            resolved_at = datetime.utcnow()

        ticket = await ticket_repo.update_status(
            ticket_id=ticket_id,
            status=status,
            resolution_notes=resolution_notes,
            resolved_at=resolved_at
        )

        if ticket:
            logger.info(f"Ticket {ticket_id} status updated to {status}")
            return ticket.to_dict()

        logger.warning(f"Ticket {ticket_id} not found for status update")
        return None

    async def escalate_ticket(
        self,
        ticket_id: UUID,
        reason: str,
        escalated_to: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Escalate a ticket to human agent.

        Args:
            ticket_id: Ticket ID to escalate
            reason: Reason for escalation
            escalated_to: Human agent email (optional)

        Returns:
            Updated ticket data or None if not found
        """
        # Update ticket status
        ticket = await self.update_ticket_status(
            ticket_id=ticket_id,
            status="escalated",
            resolution_notes=f"Escalation reason: {reason}"
        )

        if ticket and escalated_to:
            # Update conversation with escalation info
            conv = await ticket_repo.get_by_id(ticket_id)
            if conv:
                await conversation_repo.update_status(
                    conversation_id=conv.conversation_id,
                    status="escalated"
                )
                logger.info(f"Ticket {ticket_id} escalated to {escalated_to}: {reason}")

        return ticket

    async def resolve_ticket(
        self,
        ticket_id: UUID,
        resolution_notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Mark a ticket as resolved.

        Args:
            ticket_id: Ticket ID to resolve
            resolution_notes: Notes about the resolution

        Returns:
            Updated ticket data or None if not found
        """
        return await self.update_ticket_status(
            ticket_id=ticket_id,
            status="resolved",
            resolution_notes=resolution_notes
        )

    async def add_message(
        self,
        conversation_id: UUID,
        channel: str,
        direction: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[int] = None
    ) -> bool:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            channel: Message channel
            direction: Message direction (inbound/outbound)
            role: Sender role (customer/agent/system)
            content: Message content
            tokens_used: AI tokens used (for outbound)
            latency_ms: Processing time in ms

        Returns:
            True if successful
        """
        try:
            async with db.acquire() as conn:
                await conn.execute("""
                    INSERT INTO messages
                        (conversation_id, channel, direction, role, content,
                         tokens_used, latency_ms, delivery_status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    conversation_id,
                    channel,
                    direction,
                    role,
                    content,
                    tokens_used,
                    latency_ms,
                    "sent" if direction == "outbound" else "delivered"
                )

            logger.debug(f"Message added to conversation {conversation_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return False

    async def check_duplicate_ticket(
        self,
        customer_id: UUID,
        message_hash: str,
        window_minutes: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Check for duplicate tickets within time window.

        Args:
            customer_id: Customer ID
            message_hash: Hash of message content
            window_minutes: Time window in minutes

        Returns:
            Existing ticket if duplicate found, None otherwise
        """
        # This is a simplified check - in production, implement proper hashing
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT t.id, t.status, t.created_at
                FROM tickets t
                JOIN conversations c ON t.conversation_id = c.id
                WHERE c.customer_id = $1
                  AND t.created_at > NOW() - ($2 * INTERVAL '1 minute')
                  AND t.status IN ('open', 'in_progress')
                ORDER BY t.created_at DESC
                LIMIT 1
            """, customer_id, window_minutes)

            if row:
                logger.info(f"Found recent ticket {row['id']} - possible duplicate")
                return {"id": str(row["id"]), "status": row["status"]}

        return None


# Global service instance
ticket_service = TicketService()
