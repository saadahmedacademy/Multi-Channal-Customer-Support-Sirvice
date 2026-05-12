# Data Model: Multi-Channel AI Customer Support Agent

**Created**: 2026-03-25
**Feature**: 001-multi-channel
**Purpose**: Define data entities, relationships, and validation rules for the multi-channel AI customer support agent.

---

## Entity Relationship Diagram

```
┌─────────────────┐
│    Customer     │
├─────────────────┤
│ id (UUID)       │
│ email           │
│ phone           │
│ name            │
│ created_at      │
│ metadata (JSON) │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│  Conversation   │       │  CustomerIdent  │
├─────────────────┤       ├─────────────────┤
│ id (UUID)       │       │ id (UUID)       │
│ customer_id     │──────▶│ customer_id     │
│ initial_channel │       │ type            │
│ started_at      │       │ value           │
│ ended_at        │       │ verified        │
│ status          │       └─────────────────┘
│ sentiment_score │
│ metadata (JSON) │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐
│    Message      │
├─────────────────┤
│ id (UUID)       │
│ conversation_id │
│ channel         │
│ direction       │
│ role            │
│ content         │
│ created_at      │
│ tokens_used     │
│ latency_ms      │
│ tool_calls      │
│ delivery_status │
└─────────────────┘

┌─────────────────┐
│     Ticket      │
├─────────────────┤
│ id (UUID)       │
│ conversation_id │
│ customer_id     │
│ source_channel  │
│ category        │
│ priority        │
│ status          │
│ created_at      │
│ resolved_at     │
│ resolution_notes│
└─────────────────┘

┌─────────────────┐
│  KnowledgeBase  │
├─────────────────┤
│ id (UUID)       │
│ title           │
│ content         │
│ category        │
│ embedding       │
│ created_at      │
│ updated_at      │
└─────────────────┘
```

---

## Entity Definitions

### Customer

**Purpose**: Represents a person contacting support, uniquely identified by email and/or phone number.

**Fields**:
- `id` (UUID, Primary Key): Unique identifier for the customer
- `email` (VARCHAR 255, Unique, Nullable): Customer's email address (normalized: lowercase, trimmed)
- `phone` (VARCHAR 50, Unique, Nullable): Customer's phone number in E.164 format (e.g., +1234567890)
- `name` (VARCHAR 255, Nullable): Customer's display name
- `created_at` (TIMESTAMP WITH TIME ZONE): When the customer record was created
- `metadata` (JSONB): Additional customer attributes (e.g., timezone, language preference)

**Relationships**:
- Has many Conversations (1:N)
- Has many CustomerIdentifiers (1:N)
- Has many Tickets (1:N)

**Validation Rules**:
- At least one of email or phone MUST be provided
- Email MUST be valid email format
- Phone MUST be valid E.164 format if provided
- Email MUST be unique (case-insensitive)
- Phone MUST be unique

**Indexes**:
- `idx_customers_email` on email (for lookup)
- `idx_customers_phone` on phone (for lookup)

---

### CustomerIdentifier

**Purpose**: Stores multiple identifiers per customer for cross-channel recognition.

**Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `customer_id` (UUID, Foreign Key → Customer.id): Reference to customer
- `identifier_type` (VARCHAR 50): Type of identifier ('email', 'phone', 'whatsapp')
- `identifier_value` (VARCHAR 255): The actual identifier value
- `verified` (BOOLEAN): Whether this identifier has been verified
- `created_at` (TIMESTAMP WITH TIME ZONE): When this identifier was added

**Relationships**:
- Belongs to one Customer (N:1)

**Validation Rules**:
- (identifier_type, identifier_value) MUST be unique
- identifier_type MUST be one of: 'email', 'phone', 'whatsapp'
- customer_id MUST reference existing customer

**Indexes**:
- `idx_customer_identifiers_value` on identifier_value (for lookup)
- `idx_customer_identifiers_customer` on customer_id (for customer lookup)

---

### Conversation

**Purpose**: Represents a threaded discussion between a customer and the support system, potentially spanning multiple messages and channels.

**Fields**:
- `id` (UUID, Primary Key): Unique identifier for the conversation
- `customer_id` (UUID, Foreign Key → Customer.id): Reference to customer
- `initial_channel` (VARCHAR 50): Channel where conversation started ('web_form', 'whatsapp', 'email')
- `started_at` (TIMESTAMP WITH TIME ZONE): When the conversation began
- `ended_at` (TIMESTAMP WITH TIME ZONE, Nullable): When the conversation was closed
- `status` (VARCHAR 50): Current status ('active', 'closed', 'escalated')
- `sentiment_score` (DECIMAL 3,2, Nullable): Average sentiment score (-1.0 to 1.0)
- `resolution_type` (VARCHAR 50, Nullable): How conversation was resolved ('ai_resolved', 'escalated', 'customer_abandoned')
- `escalated_to` (VARCHAR 255, Nullable): Human agent email if escalated
- `metadata` (JSONB): Additional conversation attributes (e.g., tags, topics)

**Relationships**:
- Belongs to one Customer (N:1)
- Has many Messages (1:N)
- Has one Ticket (1:1, optional)

**Validation Rules**:
- customer_id MUST reference existing customer
- initial_channel MUST be one of: 'web_form', 'whatsapp', 'email'
- status MUST be one of: 'active', 'closed', 'escalated'
- sentiment_score MUST be between -1.0 and 1.0 if provided
- ended_at MUST be after started_at if both present

**Indexes**:
- `idx_conversations_customer` on customer_id
- `idx_conversations_status` on status
- `idx_conversations_initial_channel` on initial_channel
- `idx_conversations_started_at` on started_at

---

### Message

**Purpose**: Represents an individual communication (inbound from customer or outbound from AI) within a conversation.

**Fields**:
- `id` (UUID, Primary Key): Unique identifier for the message
- `conversation_id` (UUID, Foreign Key → Conversation.id): Reference to conversation
- `channel` (VARCHAR 50): Channel used for this message ('web_form', 'whatsapp', 'email')
- `direction` (VARCHAR 20): Message direction ('inbound', 'outbound')
- `role` (VARCHAR 20): Who sent the message ('customer', 'agent', 'system')
- `content` (TEXT): Message content
- `created_at` (TIMESTAMP WITH TIME ZONE): When the message was created
- `tokens_used` (INTEGER, Nullable): Number of AI tokens used (for outbound messages)
- `latency_ms` (INTEGER, Nullable): Processing time in milliseconds
- `tool_calls` (JSONB, Nullable): AI tool calls made for this message
- `channel_message_id` (VARCHAR 255, Nullable): External channel message ID (Gmail ID, Meta WhatsApp message ID)
- `delivery_status` (VARCHAR 50): Delivery status ('pending', 'sent', 'delivered', 'failed')

**Relationships**:
- Belongs to one Conversation (N:1)

**Validation Rules**:
- conversation_id MUST reference existing conversation
- channel MUST be one of: 'web_form', 'whatsapp', 'email'
- direction MUST be one of: 'inbound', 'outbound'
- role MUST be one of: 'customer', 'agent', 'system'
- content MUST NOT be empty
- delivery_status MUST be one of: 'pending', 'sent', 'delivered', 'failed'

**Indexes**:
- `idx_messages_conversation` on conversation_id
- `idx_messages_channel` on channel
- `idx_messages_created_at` on created_at
- `idx_messages_channel_message_id` on channel_message_id

---

### Ticket

**Purpose**: Represents a support request with a unique ID, status, and lifecycle tracking.

**Fields**:
- `id` (UUID, Primary Key): Unique ticket identifier (shown to customers)
- `conversation_id` (UUID, Foreign Key → Conversation.id, Unique): Reference to conversation
- `customer_id` (UUID, Foreign Key → Customer.id): Reference to customer
- `source_channel` (VARCHAR 50): Channel where ticket originated
- `category` (VARCHAR 100, Nullable): Ticket category ('general', 'technical', 'billing', 'feedback', 'bug_report')
- `priority` (VARCHAR 20): Ticket priority ('low', 'medium', 'high', 'critical')
- `status` (VARCHAR 50): Ticket status ('open', 'in_progress', 'resolved', 'escalated', 'closed')
- `created_at` (TIMESTAMP WITH TIME ZONE): When the ticket was created
- `resolved_at` (TIMESTAMP WITH TIME ZONE, Nullable): When the ticket was resolved
- `resolution_notes` (TEXT, Nullable): Notes about the resolution

**Relationships**:
- Belongs to one Conversation (1:1)
- Belongs to one Customer (N:1)

**Validation Rules**:
- conversation_id MUST reference existing conversation and be unique
- customer_id MUST reference existing customer
- source_channel MUST be one of: 'web_form', 'whatsapp', 'email'
- category MUST be one of: 'general', 'technical', 'billing', 'feedback', 'bug_report' (if provided)
- priority MUST be one of: 'low', 'medium', 'high', 'critical'
- status MUST be one of: 'open', 'in_progress', 'resolved', 'escalated', 'closed'
- resolved_at MUST be after created_at if both present

**Indexes**:
- `idx_tickets_conversation` on conversation_id
- `idx_tickets_customer` on customer_id
- `idx_tickets_status` on status
- `idx_tickets_source_channel` on source_channel
- `idx_tickets_created_at` on created_at

---

### KnowledgeBase

**Purpose**: Stores product documentation and FAQs used by the AI to generate accurate responses.

**Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `title` (VARCHAR 500): Title of the knowledge base entry
- `content` (TEXT): Content/documentation text
- `category` (VARCHAR 100, Nullable): Category ('feature', 'howto', 'faq', 'troubleshooting')
- `embedding` (VECTOR 1536): Vector embedding for semantic search (pgvector)
- `created_at` (TIMESTAMP WITH TIME ZONE): When the entry was created
- `updated_at` (TIMESTAMP WITH TIME ZONE): When the entry was last updated

**Relationships**:
- No direct relationships (referenced by AI agent)

**Validation Rules**:
- title MUST NOT be empty
- content MUST NOT be empty
- category MUST be one of: 'feature', 'howto', 'faq', 'troubleshooting' (if provided)
- embedding MUST be 1536 dimensions if provided

**Indexes**:
- `idx_knowledge_category` on category
- `idx_knowledge_embedding` on embedding USING ivfflat (vector_cosine_ops)

---

## State Transitions

### Ticket Status Transitions

```
open → in_progress → resolved → closed
                  ↘  escalated
```

**Transition Rules**:
- `open` → `in_progress`: When AI agent starts processing
- `in_progress` → `resolved`: When AI provides final response
- `in_progress` → `escalated`: When escalation trigger detected
- `resolved` → `closed`: After 24 hours with no customer follow-up
- `escalated` → `resolved`: When human agent resolves issue
- `escalated` → `closed`: When human agent closes ticket

---

### Conversation Status Transitions

```
active → closed
       ↘ escalated
```

**Transition Rules**:
- `active`: Default state when conversation starts
- `closed`: When all messages answered and no pending actions
- `escalated`: When conversation requires human intervention

---

## Validation Rules (Cross-Entity)

1. **Customer Uniqueness**: A customer can only have one record per email or phone number
2. **Conversation Continuity**: Messages from same customer within 24 hours SHOULD reuse active conversation
3. **Ticket Creation**: Every conversation MUST have exactly one ticket
4. **Message Order**: Messages MUST be queryable in chronological order
5. **Channel Consistency**: Message channel MUST match conversation's initial_channel or be a valid channel switch

---

## Database Schema (SQL)

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT chk_customers_contact CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

-- Customer identifiers for cross-channel matching
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    initial_channel VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    sentiment_score DECIMAL(3,2),
    resolution_type VARCHAR(50),
    escalated_to VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT chk_conversations_channel CHECK (initial_channel IN ('web_form', 'whatsapp', 'email')),
    CONSTRAINT chk_conversations_status CHECK (status IN ('active', 'closed', 'escalated')),
    CONSTRAINT chk_conversations_sentiment CHECK (sentiment_score BETWEEN -1.0 AND 1.0)
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    channel VARCHAR(50) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_used INTEGER,
    latency_ms INTEGER,
    tool_calls JSONB DEFAULT '[]',
    channel_message_id VARCHAR(255),
    delivery_status VARCHAR(50) DEFAULT 'pending',
    CONSTRAINT chk_messages_channel CHECK (channel IN ('web_form', 'whatsapp', 'email')),
    CONSTRAINT chk_messages_direction CHECK (direction IN ('inbound', 'outbound')),
    CONSTRAINT chk_messages_role CHECK (role IN ('customer', 'agent', 'system')),
    CONSTRAINT chk_messages_delivery CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed'))
);

-- Tickets table
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID UNIQUE REFERENCES conversations(id),
    customer_id UUID REFERENCES customers(id),
    source_channel VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    CONSTRAINT chk_tickets_channel CHECK (source_channel IN ('web_form', 'whatsapp', 'email')),
    CONSTRAINT chk_tickets_category CHECK (category IN ('general', 'technical', 'billing', 'feedback', 'bug_report')),
    CONSTRAINT chk_tickets_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_tickets_status CHECK (status IN ('open', 'in_progress', 'resolved', 'escalated', 'closed'))
);

-- Knowledge base entries
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT chk_knowledge_category CHECK (category IN ('feature', 'howto', 'faq', 'troubleshooting'))
);

-- Indexes for performance
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customer_identifiers_value ON customer_identifiers(identifier_value);
CREATE INDEX idx_customer_identifiers_customer ON customer_identifiers(customer_id);
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_initial_channel ON conversations(initial_channel);
CREATE INDEX idx_conversations_started_at ON conversations(started_at);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_channel_message_id ON messages(channel_message_id);
CREATE INDEX idx_tickets_conversation ON tickets(conversation_id);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_source_channel ON tickets(source_channel);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
CREATE INDEX idx_knowledge_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

---

## Sample Data

### Sample Customer

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@example.com",
  "phone": "+14155551234",
  "name": "John Doe",
  "created_at": "2026-03-25T10:00:00Z",
  "metadata": {
    "timezone": "America/New_York",
    "language": "en"
  }
}
```

### Sample Conversation

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "initial_channel": "web_form",
  "started_at": "2026-03-25T10:30:00Z",
  "status": "active",
  "sentiment_score": 0.8,
  "metadata": {
    "topics": ["api", "authentication"]
  }
}
```

### Sample Ticket

```json
{
  "id": "TICKET-001",
  "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_channel": "web_form",
  "category": "technical",
  "priority": "medium",
  "status": "open",
  "created_at": "2026-03-25T10:30:00Z"
}
```

### Sample Message

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "conversation_id": "660e8400-e29b-41d4-a716-446655440001",
  "channel": "web_form",
  "direction": "inbound",
  "role": "customer",
  "content": "I need help with API authentication. How do I get an API key?",
  "created_at": "2026-03-25T10:30:00Z",
  "delivery_status": "delivered"
}
```

---

## Migration Strategy

### Initial Schema (Phase 1)

- Create all tables and indexes as defined above
- Seed knowledge_base with initial documentation
- Create database user with appropriate permissions

### Future Enhancements (Post-Hackathon)

- Add full-text search indexes on message content
- Add partitioning on messages table by created_at for performance
- Add audit_log table for compliance tracking
- Add customer_feedback table for satisfaction scores
