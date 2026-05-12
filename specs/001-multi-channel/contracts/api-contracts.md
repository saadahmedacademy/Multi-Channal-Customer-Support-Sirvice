# API Contracts: Multi-Channel AI Customer Support Agent

**Created**: 2026-03-25
**Feature**: 001-multi-channel
**Purpose**: Define API endpoints, request/response schemas, and error codes for the multi-channel AI customer support agent.

---

## OpenAPI Specification (Summary)

**Base URL**: `/api`
**Content Type**: `application/json` (unless specified)

---

## Endpoints

### 1. Support Form Submission

**POST** `/support/submit`

Submit a new support request via the web form.

**Request Body**:
```json
{
  "name": "string (required, min 2 chars)",
  "email": "string (required, email format)",
  "subject": "string (required, min 5 chars)",
  "category": "string (required, one of: general, technical, billing, feedback, bug_report)",
  "priority": "string (optional, one of: low, medium, high, default: medium)",
  "message": "string (required, min 10 chars, max 1000 chars)",
  "attachments": ["string"] (optional, URLs or base64 encoded files)
}
```

**Response (200 OK)**:
```json
{
  "ticket_id": "uuid",
  "message": "Thank you for contacting us! Our AI assistant will respond shortly.",
  "estimated_response_time": "Usually within 5 minutes"
}
```

**Response (422 Validation Error)**:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

**Error Codes**:
- `400 Bad Request`: Invalid request format
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

### 2. Ticket Status Lookup

**GET** `/support/ticket/{ticket_id}`

Get the status and conversation history for a ticket.

**Path Parameters**:
- `ticket_id` (UUID): The ticket ID to look up

**Response (200 OK)**:
```json
{
  "ticket_id": "uuid",
  "status": "open | in_progress | resolved | escalated | closed",
  "category": "technical",
  "priority": "medium",
  "created_at": "2026-03-25T10:30:00Z",
  "last_updated": "2026-03-25T10:35:00Z",
  "messages": [
    {
      "id": "uuid",
      "channel": "web_form",
      "direction": "inbound | outbound",
      "role": "customer | agent | system",
      "content": "string",
      "created_at": "2026-03-25T10:30:00Z"
    }
  ]
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Ticket not found"
}
```

**Error Codes**:
- `404 Not Found`: Ticket ID doesn't exist
- `500 Internal Server Error`: Server error

---

### 3. WhatsApp Webhook

**POST** `/webhooks/whatsapp`

Receive incoming WhatsApp messages (Meta WhatsApp Cloud API webhook endpoint).

**Request Headers**:
- `X-Hub-Signature`: Signature for webhook validation

**Request Body** (JSON):
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WHATSAPP_BUSINESS_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "+1234567890",
          "phone_number_id": "PHONE_NUMBER_ID"
        },
        "messages": [{
          "from": "+14155551234",
          "id": "wamid.HBgLMTQxNTU1NTEyMzQVAgARGBI5QTNCQ0RFRjBGMUU5RjRBMTYA",
          "timestamp": "1677612345",
          "text": {
            "body": "Hello, I need help"
          },
          "type": "text"
        }]
      },
      "field": "messages"
    }]
  }]
}
```

**Response (200 OK)**:
```json
{
  "status": "received"
}
```

**Response (403 Forbidden)**:
```json
{
  "detail": "Invalid signature"
}
```

**Challenge Response (GET for webhook verification)**:
```
hub.challenge
```

**Error Codes**:
- `403 Forbidden`: Invalid webhook signature
- `400 Bad Request`: Invalid webhook payload
- `500 Internal Server Error`: Server error

**Notes**:
- Must return within 3 seconds to avoid retry
- GET request with hub.mode, hub.verify_token, hub.challenge for webhook setup verification
- POST request for actual message delivery

---

### 4. WhatsApp Message Status

**POST** `/webhooks/whatsapp/status`

Receive message delivery status updates from Meta WhatsApp Cloud API.

**Request Body** (JSON):
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WHATSAPP_BUSINESS_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "+1234567890",
          "phone_number_id": "PHONE_NUMBER_ID"
        },
        "statuses": [{
          "id": "wamid.HBgLMTQxNTU1NTEyMzQVAgARGBI5QTNCQ0RFRjBGMUU5RjRBMTYA",
          "status": "delivered",
          "timestamp": "1677612345",
          "recipient_id": "+14155551234"
        }]
      },
      "field": "messages"
    }]
  }]
}
```

**Response (200 OK)**:
```json
{
  "status": "received"
}
```

**Error Codes**:
- `400 Bad Request`: Invalid request format
- `500 Internal Server Error`: Server error

**Status Values**:
- `sent`: Message sent to WhatsApp
- `delivered`: Message delivered to customer
- `read`: Customer read the message
- `failed`: Message failed to send

---

### 5. Gmail Webhook (Optional)

**POST** `/webhooks/gmail`

Receive Gmail push notifications via Pub/Sub.

**Request Body**:
```json
{
  "message": {
    "data": "base64_encoded_notification",
    "messageId": "test-123"
  },
  "subscription": "projects/test/subscriptions/gmail-push"
}
```

**Response (200 OK)**:
```json
{
  "status": "processed",
  "count": 1
}
```

**Error Codes**:
- `400 Bad Request`: Invalid Pub/Sub message format
- `500 Internal Server Error`: Server error

---

### 6. Health Check

**GET** `/health`

Check system health and channel status.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-25T10:30:00Z",
  "channels": {
    "email": "active | inactive",
    "whatsapp": "active | inactive",
    "web_form": "active | inactive"
  },
  "services": {
    "database": "connected | disconnected",
    "queue": "connected | disconnected",
    "ai_api": "connected | disconnected"
  }
}
```

**Error Codes**:
- `503 Service Unavailable`: One or more critical services down

---

### 7. Customer Lookup

**GET** `/customers/lookup`

Look up a customer by email or phone number.

**Query Parameters**:
- `email` (string, optional): Customer email address
- `phone` (string, optional): Customer phone number

**Response (200 OK)**:
```json
{
  "id": "uuid",
  "email": "john@example.com",
  "phone": "+14155551234",
  "name": "John Doe",
  "created_at": "2026-03-25T10:00:00Z",
  "conversations": [
    {
      "id": "uuid",
      "initial_channel": "web_form",
      "started_at": "2026-03-25T10:30:00Z",
      "status": "active"
    }
  ]
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Customer not found"
}
```

**Response (400 Bad Request)**:
```json
{
  "detail": "Provide email or phone parameter"
}
```

**Error Codes**:
- `400 Bad Request`: Missing email and phone parameters
- `404 Not Found`: Customer not found
- `500 Internal Server Error`: Server error

---

### 8. Channel Metrics

**GET** `/metrics/channels`

Get performance metrics broken down by channel.

**Response (200 OK)**:
```json
{
  "web_form": {
    "channel": "web_form",
    "total_conversations": 150,
    "avg_sentiment": 0.75,
    "escalations": 12,
    "avg_response_time_ms": 45000
  },
  "whatsapp": {
    "channel": "whatsapp",
    "total_conversations": 200,
    "avg_sentiment": 0.68,
    "escalations": 25,
    "avg_response_time_ms": 38000
  },
  "email": {
    "channel": "email",
    "total_conversations": 50,
    "avg_sentiment": 0.72,
    "escalations": 8,
    "avg_response_time_ms": 52000
  }
}
```

**Error Codes**:
- `500 Internal Server Error`: Server error

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "string | object",
  "error_code": "string (optional)",
  "ticket_id": "uuid (optional, for tracking)"
}
```

For validation errors (422):
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

---

## Rate Limiting

**Default Limits**:
- Web form submissions: 10 per minute per IP
- WhatsApp messages: As per Meta limits (1000 messages per 24-hour rolling window for free tier)
- Ticket status lookups: 60 per minute per IP
- API endpoints: 100 requests per minute per IP

**Rate Limit Response (429 Too Many Requests)**:
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

---

## Authentication

**Internal APIs** (customer-facing): No authentication required (public endpoints)

**Admin APIs** (future): API key or JWT token required

**Webhook Validation**:
- WhatsApp: X-Hub-Signature header validation (Meta)
- Gmail: Pub/Sub message attribute validation

---

## Versioning

API version is included in the path: `/api/v1/...`

Current version: `v1` (implicit, no version prefix for hackathon)

Breaking changes will require version bump to `/api/v2/...`

---

## CORS Configuration

**Allowed Origins**: `*` (for hackathon; restrict in production)

**Allowed Methods**: `GET, POST, OPTIONS`

**Allowed Headers**: `Content-Type, X-Hub-Signature, Authorization`

**Max Age**: 600 seconds

---

## Request/Response Examples

### Example 1: Web Form Submission

**Request**:
```bash
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "API Authentication Help",
    "category": "technical",
    "message": "I need help with API authentication. How do I get an API key?"
  }'
```

**Response**:
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Thank you for contacting us! Our AI assistant will respond shortly.",
  "estimated_response_time": "Usually within 5 minutes"
}
```

---

### Example 2: Ticket Status Check

**Request**:
```bash
curl http://localhost:8000/support/ticket/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "category": "technical",
  "priority": "medium",
  "created_at": "2026-03-25T10:30:00Z",
  "last_updated": "2026-03-25T10:35:00Z",
  "messages": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "channel": "web_form",
      "direction": "inbound",
      "role": "customer",
      "content": "I need help with API authentication. How do I get an API key?",
      "created_at": "2026-03-25T10:30:00Z"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440003",
      "channel": "web_form",
      "direction": "outbound",
      "role": "agent",
      "content": "Hi John! To get an API key, navigate to Settings > API in your dashboard. Click 'Generate New Key' and copy it securely.",
      "created_at": "2026-03-25T10:32:00Z"
    }
  ]
}
```

---

### Example 3: WhatsApp Message (Webhook)

**Request**:
```bash
curl -X POST http://localhost:8000/webhooks/whatsapp \
  -H "X-Hub-Signature: sha256=abc123signature" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "WHATSAPP_BUSINESS_ID",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "metadata": {
            "display_phone_number": "+1234567890",
            "phone_number_id": "PHONE_NUMBER_ID"
          },
          "messages": [{
            "from": "+14155551234",
            "id": "wamid.HBgLMTQxNTU1NTEyMzQVAgARGBI5QTNCQ0RFRjBGMUU5RjRBMTYA",
            "timestamp": "1677612345",
            "text": {
              "body": "Hi, I need help with my account"
            },
            "type": "text"
          }]
        },
        "field": "messages"
      }]
    }]
  }'
```

**Response**:
```json
{
  "status": "received"
}
```

---

## Schema Definitions (Pydantic)

### SupportFormSubmission

```python
class SupportFormSubmission(BaseModel):
    name: str = Field(..., min_length=2, description="Customer name")
    email: EmailStr = Field(..., description="Customer email")
    subject: str = Field(..., min_length=5, description="Subject line")
    category: Literal["general", "technical", "billing", "feedback", "bug_report"]
    priority: Literal["low", "medium", "high"] = "medium"
    message: str = Field(..., min_length=10, max_length=1000)
    attachments: Optional[List[str]] = []
```

### SupportFormResponse

```python
class SupportFormResponse(BaseModel):
    ticket_id: UUID
    message: str
    estimated_response_time: str
```

### TicketStatusResponse

```python
class MessageSchema(BaseModel):
    id: UUID
    channel: str
    direction: str
    role: str
    content: str
    created_at: datetime

class TicketStatusResponse(BaseModel):
    ticket_id: UUID
    status: Literal["open", "in_progress", "resolved", "escalated", "closed"]
    category: Optional[str]
    priority: str
    created_at: datetime
    last_updated: datetime
    messages: List[MessageSchema]
```

### CustomerLookupResponse

```python
class ConversationSummary(BaseModel):
    id: UUID
    initial_channel: str
    started_at: datetime
    status: str

class CustomerLookupResponse(BaseModel):
    id: UUID
    email: Optional[str]
    phone: Optional[str]
    name: Optional[str]
    created_at: datetime
    conversations: List[ConversationSummary]
```

### HealthCheckResponse

```python
class ServiceStatus(BaseModel):
    database: Literal["connected", "disconnected"]
    queue: Literal["connected", "disconnected"]
    ai_api: Literal["connected", "disconnected"]

class ChannelStatus(BaseModel):
    email: Literal["active", "inactive"]
    whatsapp: Literal["active", "inactive"]
    web_form: Literal["active", "inactive"]

class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    channels: ChannelStatus
    services: ServiceStatus
```

---

## Testing Guidelines

### Contract Tests

1. **Schema Validation**: Verify all request/response schemas validate correctly
2. **Error Handling**: Verify error responses match documented format
3. **Status Codes**: Verify correct HTTP status codes for all scenarios
4. **Headers**: Verify required headers (Content-Type, CORS)

### Integration Tests

1. **End-to-End Flow**: Submit form → Queue → Worker → Response → Ticket status update
2. **Webhook Processing**: WhatsApp webhook → Queue → Worker → Response
3. **Customer Identification**: Same customer across channels → Unified history

### Test Data

Use test fixtures for:
- Valid/invalid form submissions
- WhatsApp webhook payloads
- Customer/conversation/ticket records
- Knowledge base entries
