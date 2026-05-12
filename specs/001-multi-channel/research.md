# Research: Multi-Channel AI Customer Support Agent

**Created**: 2026-03-25
**Feature**: 001-multi-channel
**Purpose**: Document technical decisions, best practices, and integration patterns for the multi-channel AI customer support agent.

---

## Technology Decisions

### Decision 1: Queue Technology - Redpanda over Kafka

**Decision**: Use Redpanda (single-node) for message queuing

**Rationale**:
- Constitution Principle II forbids heavy infrastructure
- Redpanda is Kafka-compatible but 10x lighter weight
- Single binary deployment, no Zookeeper dependency
- Runs comfortably on 4GB RAM
- Provides same async processing guarantees as Kafka

**Alternatives Considered**:
- Apache Kafka: Too heavy, requires Zookeeper, complex operations
- RabbitMQ: Good alternative but less stream-oriented
- AWS SQS: Cloud vendor lock-in, adds latency
- In-memory queue: No persistence, loses messages on restart

**Best Practices**:
- Run Redpanda in single-node mode for hackathon
- Enable persistence to survive restarts
- Use topics: `tickets.incoming`, `tickets.outgoing`, `escalations`
- Configure retention: 7 days for debugging
- Monitor queue depth for backpressure detection

---

### Decision 2: AI API - OpenRouter as Primary, Gemini as Fallback

**Decision**: Use OpenRouter API for AI responses with Google Gemini as fallback

**Rationale**:
- Constitution requires cloud APIs only (no local LLMs)
- OpenRouter provides unified API to multiple models
- Automatic fallback if primary model unavailable
- Cost-effective pricing for hackathon scale
- No infrastructure management required

**Alternatives Considered**:
- Google Gemini only: Good but single provider risk
- OpenAI GPT: Higher cost, API availability issues
- Local LLM (Ollama): Forbidden by constitution (resource-heavy)
- Anthropic Claude: Good but expensive for hackathon budget

**Best Practices**:
- Implement retry logic with exponential backoff
- Cache common responses to reduce API calls
- Set reasonable timeout (30 seconds)
- Log all AI requests for debugging
- Implement fallback to generic response on API failure

---

### Decision 3: Database - Supabase PostgreSQL

**Decision**: Use Supabase (managed PostgreSQL) for data persistence

**Rationale**:
- Constitution specifies Supabase as required technology
- PostgreSQL with pgvector for semantic search
- Managed service reduces operational complexity
- Free tier sufficient for hackathon
- Built-in connection pooling

**Alternatives Considered**:
- Self-hosted PostgreSQL: More ops work, no pgvector by default
- MongoDB: Less suitable for relational conversation data
- SQLite: Not suitable for concurrent access
- Firebase: No pgvector, vendor lock-in

**Best Practices**:
- Use connection pooling (asyncpg with pool size 10)
- Enable pgvector extension for semantic search
- Index frequently queried columns (customer_id, ticket_id, status)
- Use UUIDs for all primary keys
- Implement soft deletes for audit trail

---

### Decision 4: Backend Framework - FastAPI

**Decision**: Use FastAPI for backend API

**Rationale**:
- Constitution specifies FastAPI as required technology
- Native async/await support for queue processing
- Automatic OpenAPI documentation
- Pydantic integration for validation
- High performance, low memory footprint

**Alternatives Considered**:
- Flask: Synchronous, slower performance
- Django: Too heavy for hackathon needs
- Starlette: Lower level, FastAPI builds on it
- Node.js/Express: Team expertise in Python

**Best Practices**:
- Use dependency injection for database connections
- Implement global exception handlers
- Use Pydantic schemas for all request/response validation
- Enable CORS for frontend integration
- Use BackgroundTasks for non-blocking operations

---

### Decision 5: Frontend - Next.js App Router

**Decision**: Use Next.js with App Router for support form UI

**Rationale**:
- Constitution specifies Next.js as required technology
- Server-side rendering for fast initial load
- API routes for secure backend communication
- React ecosystem for component reusability
- Easy deployment to Vercel or self-hosted

**Alternatives Considered**:
- React SPA: Slower initial load, separate API needed
- Vue/Nuxt: Team expertise in React
- Plain HTML/JS: Too manual, lacks modern DX
- SvelteKit: Less mature ecosystem

**Best Practices**:
- Use server actions for form submission
- Implement optimistic UI updates
- Add loading states for better UX
- Validate on client and server
- Use TypeScript for type safety

---

## Integration Patterns

### Pattern 1: WhatsApp Cloud API Integration (Meta)

**Approach**: Webhook-based message reception, Graph API for sending

**Flow**:
1. WhatsApp sends POST to `/api/webhooks/whatsapp` on message received (Meta Cloud API)
2. Webhook validates X-Hub-Signature and extracts message data
3. Message published to `tickets.incoming` Redpanda topic
4. Worker processes message and generates response
5. Response sent via Meta Graph API POST request

**Best Practices**:
- Validate webhook signature (X-Hub-Signature-256)
- Return 200 OK within 3 seconds to avoid retry
- Handle media messages gracefully (acknowledge, escalate)
- Free tier: 1000 messages per 24-hour rolling window
- Store WhatsApp message ID for delivery tracking
- Use GET request with hub.challenge for webhook verification

**Error Handling**:
- Webhook validation failure → 403 Forbidden
- API rate limit → Queue for retry with backoff
- Invalid phone number → Log error, send error message
- API downtime → Queue message, retry every 5 minutes

---

### Pattern 2: Async Message Processing

**Approach**: Queue-based processing with worker pool

**Flow**:
1. API receives message (web form or WhatsApp)
2. API publishes to Redpanda topic `tickets.incoming`
3. Worker subscribes and processes messages concurrently
4. Worker calls AI API, stores response, sends to customer
5. Metrics published to `metrics` topic for monitoring

**Best Practices**:
- Use consumer groups for parallel processing
- Commit offsets after successful processing
- Implement dead letter queue for failed messages
- Monitor consumer lag for scaling decisions
- Graceful shutdown on SIGTERM

**Error Handling**:
- AI API timeout → Retry with exponential backoff (max 3)
- Database connection failure → Retry, then dead letter
- Invalid message format → Log, acknowledge, skip
- Worker crash → Message reprocessed by another worker

---

### Pattern 3: Cross-Channel Customer Identification

**Approach**: Email/phone-based customer matching

**Flow**:
1. Extract identifiers from incoming message (email from web form, phone from WhatsApp)
2. Query customers table for match
3. If found, load conversation history across all channels
4. If not found, create new customer record
5. Link conversation to customer for future continuity

**Best Practices**:
- Normalize phone numbers (E.164 format: +1234567890)
- Lowercase and trim email addresses
- Use unique constraint on email for deduplication
- Store multiple identifiers per customer
- Handle identifier merging (same customer, new phone)
- Meta WhatsApp provides phone number in E.164 format

**Edge Cases**:
- Same email, different phone → Merge into one customer
- Same phone, different email → Merge into one customer
- No identifiers → Create anonymous customer with session ID

---

### Pattern 4: Escalation Handling

**Approach**: Rule-based escalation with human queue

**Escalation Triggers**:
- Keywords: "pricing", "refund", "lawyer", "legal", "sue"
- Sentiment score < 0.3 (angry/frustrated)
- Explicit request: "human", "agent", "representative"
- AI confidence < 0.5 (uncertain response)

**Flow**:
1. Worker detects escalation trigger
2. Generate empathetic response: "A human agent will contact you shortly"
3. Update ticket status to "escalated"
4. Publish to `escalations` topic for human agent dashboard
5. Optionally send email notification to support team

**Best Practices**:
- Log escalation reason for analytics
- Prioritize escalations by sentiment severity
- Set SLA for human response (e.g., 1 hour)
- Provide full conversation context to human agent
- Allow human to mark escalation as resolved

---

### Pattern 5: Graceful Degradation

**Approach**: Fallback responses when services unavailable

**Failure Scenarios**:
- AI API down → Use canned responses based on category
- Database down → Queue messages, respond with delay notice
- Queue down → Synchronous processing with timeout
- WhatsApp API down → Store messages, retry later

**Fallback Response Examples**:
- "Thanks for contacting us! Our systems are experiencing high volume. A human agent will respond within 2 hours."
- "We received your message and will respond as soon as possible. Your ticket ID is: {{ticket_id}}"

**Best Practices**:
- Never expose internal errors to customers
- Always provide ticket ID for tracking
- Log all failures with full context
- Implement circuit breaker pattern for external APIs
- Monitor error rates and alert on thresholds

---

## Performance Optimization

### Low-Resource Optimization (4GB RAM)

**Memory Budget**:
- Redpanda: 512MB
- PostgreSQL (Supabase): External (no local memory)
- FastAPI: 256MB
- Worker: 512MB
- Next.js: 256MB
- OS + Buffer: 1.5GB

**Optimization Techniques**:
- Use async I/O throughout (asyncpg, aiohttp)
- Limit connection pool sizes (10 max)
- Stream large responses instead of buffering
- Use generators for iteration
- Cache frequently accessed data (knowledge base)
- Avoid loading entire conversation history (last 10 messages)

---

## Security Considerations

### Data Protection

- Use environment variables for all secrets (never hardcode)
- Enable HTTPS for all endpoints (Let's Encrypt)
- Validate and sanitize all user input
- Use parameterized queries (prevent SQL injection)
- Implement rate limiting (prevent abuse)
- Log access to customer data (audit trail)

### API Security

- Validate WhatsApp webhook signatures (X-Hub-Signature-256 from Meta)
- Use API keys for internal service communication
- Implement CORS policies for frontend
- Use HTTPS for all external API calls (Meta Graph API)
- Rotate API keys regularly

---

## Monitoring & Observability

### Key Metrics to Track

- **Queue Depth**: Messages waiting in `tickets.incoming`
- **Processing Time**: Time from message receipt to response delivery
- **Error Rate**: Percentage of messages failing processing
- **Escalation Rate**: Percentage of conversations escalated
- **AI API Latency**: Response time from AI provider
- **Customer Recognition Rate**: Percentage of returning customers identified

### Logging Strategy

- Structured JSON logging (machine-parseable)
- Include correlation IDs (ticket_id, conversation_id)
- Log levels: INFO (normal), WARN (recoverable), ERROR (actionable)
- Redact PII (email, phone) from logs
- Centralized log aggregation for debugging

---

## Testing Strategy

### Unit Tests

- Test individual functions in isolation
- Mock external dependencies (AI API, WhatsApp API)
- Test escalation logic with various triggers
- Test sentiment analysis edge cases

### Integration Tests

- Test full flow: Web form → Queue → Worker → AI → Response
- Test WhatsApp webhook → Queue → Worker → WhatsApp response
- Test cross-channel customer identification
- Test escalation flow end-to-end

### Contract Tests

- Verify API request/response schemas
- Test WhatsApp webhook payload structure
- Verify database schema constraints

### Load Tests

- Verify system handles 100 concurrent submissions
- Test queue processing under load
- Verify response times meet SLA (<2 minutes)

---

## Deployment Strategy

### Local Development

- Docker Compose for Redpanda (single container)
- Local FastAPI with hot reload
- Local Next.js development server
- Supabase local development or cloud dev instance

### Hackathon Deployment

**Option A: Single VPS**
- Deploy Redpanda, FastAPI, Worker, Next.js on single 4GB VM
- Use Docker Compose for orchestration
- Supabase hosted externally
- Nginx reverse proxy for routing

**Option B: Hybrid Cloud**
- Vercel for Next.js frontend (free tier)
- Railway/Render for FastAPI backend (free tier)
- Supabase for database (free tier)
- Redpanda on small VM or Confluent Cloud free tier

**Recommended**: Option A for simplicity and low-resource compliance

---

## Open Questions (Resolved)

### Q1: How to handle customer identification across channels?

**Resolved**: Use email as primary identifier for web form, phone for WhatsApp. Allow linking multiple identifiers to single customer record. Match on normalized email (lowercase, trimmed) or phone (E.164 format).

### Q2: What is the escalation threshold for sentiment analysis?

**Resolved**: Sentiment score < 0.3 triggers escalation. Use pre-trained sentiment model (e.g., Hugging Face transformers via API) or simple keyword-based detection as fallback.

### Q3: How to handle messages received outside business hours?

**Resolved**: System operates 24/7. AI handles all inquiries automatically. Escalations queued for next business day with appropriate customer messaging about expected response time.

### Q4: What knowledge base format to use?

**Resolved**: JSON format with title, content, category fields. Simple structure for easy maintenance. Can migrate to vector database later if needed.

---

## References

- [Redpanda Documentation](https://docs.redpanda.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Meta WhatsApp Cloud API Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Meta Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [OpenRouter Documentation](https://openrouter.ai/docs)
