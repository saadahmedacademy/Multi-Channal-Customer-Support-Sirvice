"""Conversation database model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal


@dataclass
class Conversation:
    """Represents a conversation thread with a customer."""
    
    id: UUID
    customer_id: UUID
    initial_channel: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str = "active"
    sentiment_score: Optional[Decimal] = None
    resolution_type: Optional[str] = None
    escalated_to: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_row(cls, row: dict) -> "Conversation":
        """Create a Conversation instance from a database row."""
        return cls(
            id=row["id"],
            customer_id=row["customer_id"],
            initial_channel=row["initial_channel"],
            started_at=row["started_at"],
            ended_at=row.get("ended_at"),
            status=row.get("status", "active"),
            sentiment_score=row.get("sentiment_score"),
            resolution_type=row.get("resolution_type"),
            escalated_to=row.get("escalated_to"),
            metadata=row.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "id": str(self.id),
            "customer_id": str(self.customer_id),
            "initial_channel": self.initial_channel,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "sentiment_score": float(self.sentiment_score) if self.sentiment_score else None,
            "resolution_type": self.resolution_type,
            "escalated_to": self.escalated_to,
            "metadata": self.metadata or {}
        }
