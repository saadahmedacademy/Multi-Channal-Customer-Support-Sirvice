"""Pydantic schemas for ticket operations."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class TicketCategory(str, Enum):
    """Ticket categories."""
    GENERAL = "general"
    TECHNICAL = "technical"
    BILLING = "billing"
    FEEDBACK = "feedback"
    BUG_REPORT = "bug_report"


class TicketPriority(str, Enum):
    """Ticket priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    """Ticket statuses."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class SupportFormSubmission(BaseModel):
    """Request schema for web support form submission."""
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    email: EmailStr = Field(..., description="Customer email address")
    phone: Optional[str] = Field(None, max_length=50, description="Customer phone number (E.164 format)")
    subject: str = Field(..., min_length=1, max_length=500, description="Subject of the inquiry")
    category: TicketCategory = Field(..., description="Category of the issue")
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM, description="Priority level")
    message: str = Field(..., min_length=1, max_length=5000, description="Detailed message")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+14155551234",
                "subject": "API Authentication Issue",
                "category": "technical",
                "priority": "medium",
                "message": "I'm having trouble authenticating with the API. Getting 401 errors."
            }
        }


class SupportFormResponse(BaseModel):
    """Response schema for successful form submission."""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    message: str = Field(..., description="Confirmation message")
    estimated_response_time: str = Field(..., description="Expected response time")
    status: TicketStatus = Field(..., description="Initial ticket status")

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TICKET-001",
                "message": "Thank you for contacting us! Our AI assistant will respond shortly.",
                "estimated_response_time": "Within 2 minutes",
                "status": "open"
            }
        }


class SurveyRating(str, Enum):
    """Survey rating options."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class SurveySubmitRequest(BaseModel):
    """Request schema for survey submission."""
    rating: SurveyRating = Field(..., description="Thumbs up or down")
    reason: Optional[str] = Field(None, max_length=500, description="Optional feedback reason")

    class Config:
        json_schema_extra = {
            "example": {
                "rating": "thumbs_up",
                "reason": None
            }
        }


class SurveyResponse(BaseModel):
    """Response schema for survey."""
    id: str = Field(..., description="Survey ID")
    ticket_id: str = Field(..., description="Ticket ID")
    rating: SurveyRating = Field(..., description="Survey rating")
    reason: Optional[str] = Field(None, description="Feedback reason")
    source: str = Field(..., description="Submission channel")
    created_at: datetime = Field(..., description="When survey was submitted")


class TicketStatusResponse(BaseModel):
    """Response schema for ticket status lookup."""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    status: TicketStatus = Field(..., description="Current ticket status")
    category: Optional[TicketCategory] = Field(None, description="Ticket category")
    priority: TicketPriority = Field(..., description="Ticket priority")
    created_at: datetime = Field(..., description="When the ticket was created")
    resolved_at: Optional[datetime] = Field(None, description="When the ticket was resolved")
    messages: list = Field(default_factory=list, description="Conversation messages")
    resolution_notes: Optional[str] = Field(None, description="Notes about resolution")
    survey: Optional[SurveyResponse] = Field(None, description="Post-resolution survey")

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TICKET-001",
                "status": "resolved",
                "category": "technical",
                "priority": "medium",
                "created_at": "2026-03-25T10:30:00Z",
                "resolved_at": "2026-03-25T10:32:00Z",
                "messages": [
                    {
                        "role": "customer",
                        "content": "I need help with API authentication",
                        "created_at": "2026-03-25T10:30:00Z"
                    },
                    {
                        "role": "agent",
                        "content": "I'd be happy to help you with API authentication...",
                        "created_at": "2026-03-25T10:32:00Z"
                    }
                ],
                "resolution_notes": "Provided API key setup instructions"
            }
        }


class TicketListResponse(BaseModel):
    """Response schema for listing tickets."""
    tickets: list[TicketStatusResponse] = Field(..., description="List of tickets")
    total: int = Field(..., description="Total number of tickets")


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
