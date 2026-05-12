"""Message database model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


@dataclass
class Message:
    """Represents a message in a conversation."""
    
    id: UUID
    conversation_id: UUID
    channel: str
    direction: str
    role: str
    content: str
    created_at: datetime
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    channel_message_id: Optional[str] = None
    delivery_status: str = "pending"
    
    @classmethod
    def from_row(cls, row: dict) -> "Message":
        """Create a Message instance from a database row."""
        return cls(
            id=row["id"],
            conversation_id=row["conversation_id"],
            channel=row["channel"],
            direction=row["direction"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
            tokens_used=row.get("tokens_used"),
            latency_ms=row.get("latency_ms"),
            tool_calls=row.get("tool_calls", []),
            channel_message_id=row.get("channel_message_id"),
            delivery_status=row.get("delivery_status", "pending")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "channel": self.channel,
            "direction": self.direction,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "tool_calls": self.tool_calls or [],
            "channel_message_id": self.channel_message_id,
            "delivery_status": self.delivery_status
        }
