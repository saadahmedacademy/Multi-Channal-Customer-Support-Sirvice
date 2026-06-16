"""Pydantic schemas for message and conversation operations."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class MessageRole(str, Enum):
    """Message sender roles."""
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"


class MessageDirection(str, Enum):
    """Message direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Channel(str, Enum):
    """Communication channels."""
    WEB_FORM = "web_form"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class FeedbackRating(str, Enum):
    """Message feedback rating."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class DeliveryStatus(str, Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class MessageSchema(BaseModel):
    """Schema for individual messages."""
    id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Parent conversation ID")
    channel: Channel = Field(..., description="Channel used for this message")
    direction: MessageDirection = Field(..., description="Message direction")
    role: MessageRole = Field(..., description="Who sent the message")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="When the message was created")
    tokens_used: Optional[int] = Field(None, description="AI tokens used (for outbound)")
    latency_ms: Optional[int] = Field(None, description="Processing time in ms")
    delivery_status: DeliveryStatus = Field(..., description="Delivery status")
    feedback: Optional[FeedbackRating] = Field(None, description="Thumbs up/down feedback")
    feedback_reason: Optional[str] = Field(None, description="Optional reason for thumbs down")
    feedback_created_at: Optional[datetime] = Field(None, description="When feedback was given")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-001",
                "conversation_id": "conv-001",
                "channel": "web_form",
                "direction": "inbound",
                "role": "customer",
                "content": "I need help with API authentication",
                "created_at": "2026-03-25T10:30:00Z",
                "delivery_status": "delivered"
            }
        }


class ConversationSchema(BaseModel):
    """Schema for conversations."""
    id: str = Field(..., description="Unique conversation identifier")
    customer_id: str = Field(..., description="Customer ID")
    initial_channel: Channel = Field(..., description="Channel where conversation started")
    started_at: datetime = Field(..., description="When the conversation began")
    ended_at: Optional[datetime] = Field(None, description="When the conversation ended")
    status: str = Field(..., description="Conversation status (active/closed/escalated)")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Average sentiment")
    messages: list[MessageSchema] = Field(default_factory=list, description="Conversation messages")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "conv-001",
                "customer_id": "cust-001",
                "initial_channel": "web_form",
                "started_at": "2026-03-25T10:30:00Z",
                "status": "active",
                "sentiment_score": 0.8,
                "messages": []
            }
        }


class MessageCreate(BaseModel):
    """Request schema for creating a message."""
    conversation_id: str = Field(..., description="Parent conversation ID")
    channel: Channel = Field(..., description="Channel used")
    direction: MessageDirection = Field(..., description="Message direction")
    role: MessageRole = Field(..., description="Sender role")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-001",
                "channel": "web_form",
                "direction": "inbound",
                "role": "customer",
                "content": "I need help with API authentication"
            }
        }


class FeedbackSubmit(BaseModel):
    """Request schema for submitting message feedback."""
    rating: FeedbackRating = Field(..., description="Thumbs up or down")
    reason: Optional[str] = Field(None, max_length=500, description="Optional reason for thumbs down")

    class Config:
        json_schema_extra = {
            "example": {
                "rating": "thumbs_up",
                "reason": None
            }
        }


class FollowUpMessage(BaseModel):
    """Request schema for follow-up message in existing conversation."""
    conversation_id: str = Field(..., description="Parent conversation ID")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv-001",
                "content": "Can you provide more details about the API setup?"
            }
        }


class FollowUpResponse(BaseModel):
    """Response schema for follow-up message."""
    message_id: str = Field(..., description="New message ID")
    response_message_id: str = Field(..., description="AI response message ID")
    response: str = Field(..., description="AI response content")
    tokens_used: int = Field(..., description="AI tokens consumed")
    created_at: datetime = Field(..., description="When the response was created")


class AIResponseRequest(BaseModel):
    """Request schema for AI response generation."""
    message: str = Field(..., description="Customer message")
    conversation_history: list[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous messages in conversation"
    )
    channel: Channel = Field(..., description="Channel for response formatting")
    knowledge_context: list[Dict[str, str]] = Field(
        default_factory=list,
        description="Relevant knowledge base entries"
    )
    customer_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Customer metadata (timezone, language, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "How do I get an API key?",
                "conversation_history": [],
                "channel": "web_form",
                "knowledge_context": [
                    {"title": "API Keys", "content": "API keys can be generated..."}
                ]
            }
        }


class AIResponse(BaseModel):
    """Response schema for AI-generated responses."""
    response: str = Field(..., description="AI-generated response text")
    escalation_required: bool = Field(..., description="Whether escalation is needed")
    escalation_reason: Optional[str] = Field(None, description="Reason for escalation")
    sentiment_score: Optional[float] = Field(None, description="Detected sentiment")
    tokens_used: int = Field(..., description="AI tokens consumed")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Response confidence")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "To get an API key, please follow these steps...",
                "escalation_required": False,
                "sentiment_score": 0.8,
                "tokens_used": 150,
                "confidence": 0.95
            }
        }
