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
