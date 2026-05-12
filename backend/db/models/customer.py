"""Customer database model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class Customer:
    """Represents a customer in the support system."""
    
    id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate that at least one contact method is provided."""
        if not self.email and not self.phone:
            raise ValueError("Customer must have at least email or phone")
    
    @classmethod
    def from_row(cls, row: dict) -> "Customer":
        """Create a Customer instance from a database row."""
        return cls(
            id=row["id"],
            email=row.get("email"),
            phone=row.get("phone"),
            name=row.get("name"),
            created_at=row.get("created_at"),
            metadata=row.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customer to dictionary."""
        return {
            "id": str(self.id),
            "email": self.email,
            "phone": self.phone,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata or {}
        }
