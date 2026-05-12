"""Ticket database model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class Ticket:
    """Represents a support ticket."""
    
    id: UUID
    conversation_id: UUID
    customer_id: UUID
    source_channel: str
    category: Optional[str] = None
    priority: str = "medium"
    status: str = "open"
    created_at: datetime = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    def __post_init__(self):
        """Set created_at if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @classmethod
    def from_row(cls, row: dict) -> "Ticket":
        """Create a Ticket instance from a database row."""
        return cls(
            id=row["id"],
            conversation_id=row["conversation_id"],
            customer_id=row["customer_id"],
            source_channel=row["source_channel"],
            category=row.get("category"),
            priority=row.get("priority", "medium"),
            status=row.get("status", "open"),
            created_at=row["created_at"],
            resolved_at=row.get("resolved_at"),
            resolution_notes=row.get("resolution_notes")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ticket to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "customer_id": str(self.customer_id),
            "source_channel": self.source_channel,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes
        }
