# Quickstart: Multi-Channel AI Customer Support Agent

**Created**: 2026-03-25
**Feature**: 001-multi-channel
**Purpose**: Get the multi-channel AI customer support agent running locally in under 10 minutes.

---

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker (for Redpanda)
- Git
- Supabase account (free tier)
- OpenRouter API key (or Google Gemini API key)
- WhatsApp Cloud API credentials (for WhatsApp support)

---

## Step 1: Clone and Setup

```bash
# Clone the repository
cd /home/saadahmed/hk-5

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

---

## Step 2: Environment Configuration

Create `.env` file in the project root:

```bash
# Database (Supabase)
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=[your-anon-key]

# AI API
OPENROUTER_API_KEY=sk-or-[your-key]
# OR (for Gemini fallback)
GEMINI_API_KEY=[your-gemini-key]

# WhatsApp (Meta Cloud API - Free Tier)
META_WHATSAPP_TOKEN=[your-access-token]
META_WHATSAPP_PHONE_ID=[your-phone-id]
META_WHATSAPP_BUSINESS_ID=[your-business-id]

# Redpanda (Kafka-compatible)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=[generate-random-string]
```

**Generate SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 3: Start Redpanda (Message Queue)

```bash
# Start Redpanda in Docker
docker run -d --name redpanda \
  -p 9092:9092 \
  -p 28081:28081 \
  docker.redpanda.com/redpandadata/redpanda:latest \
  redpanda start \
  --smp 1 \
  --memory 512M \
  --overprovisioned \
  --node-id 0 \
  --kafka-addr PLAINTEXT://0.0.0.0:29092,OUTSIDE://0.0.0.0:9092 \
  --advertise-kafka-addr PLAINTEXT://redpanda:29092,OUTSIDE://localhost:9092 \
  --pandaproxy-addr 0.0.0.0:8082 \
  --advertise-pandaproxy-addr localhost:8082
```

**Verify Redpanda is running**:
```bash
docker ps | grep redpanda
```

**Create Kafka topics**:
```bash
# Install kafka-cli tools or use Python script
python backend/scripts/create-topics.py
```

Topics created:
- `tickets.incoming`
- `tickets.outgoing`
- `escalations`
- `metrics`

---

## Step 4: Setup Database (Supabase)

```bash
# Run database migrations
psql $DATABASE_URL -f database/schema.sql

# Seed knowledge base (optional)
psql $DATABASE_URL -f database/seed.sql
```

**Verify database setup**:
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM customers;"
```

Expected output: `0` (empty table)

---

## Step 5: Start Backend (FastAPI)

```bash
# From project root, with virtual environment activated
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify backend is running**:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-25T10:00:00Z",
  "channels": {
    "email": "active",
    "whatsapp": "active",
    "web_form": "active"
  }
}
```

**Open API Documentation**: http://localhost:8000/docs

---

## Step 6: Start Worker (Message Processor)

Open a new terminal:

```bash
cd /home/saadahmed/hk-5
source .venv/bin/activate

# Start the message processor worker
python backend/worker/message_processor.py
```

**Verify worker is running**:
You should see logs like:
```
INFO: Message processor started, listening for tickets...
INFO: Connected to Redpanda at localhost:9092
```

---

## Step 7: Start Frontend (Next.js)

Open another terminal:

```bash
cd /home/saadahmed/hk-5/frontend
npm run dev
```

**Verify frontend is running**:
```
Ready in 2.5s
○ Compiling / ...
✓ Compiled / in 1.2s
```

**Open in browser**: http://localhost:3000

---

## Step 8: Test the System

### Test 1: Web Form Submission

1. Open http://localhost:3000 in your browser
2. Fill out the support form:
   - Name: Test User
   - Email: test@example.com
   - Subject: Test Question
   - Category: technical
   - Message: This is a test message to verify the system works
3. Click "Submit Support Request"
4. Note the ticket ID returned

**Expected Result**:
- Confirmation message with ticket ID
- "Thank you for contacting us! Our AI assistant will respond shortly."

### Test 2: Check Ticket Status

```bash
# Replace TICKET_ID with the ID from step 1
curl http://localhost:8000/support/ticket/TICKET_ID
```

**Expected Result**:
- Ticket status: `open` or `in_progress`
- Messages array with your submission

### Test 3: Verify AI Response

Wait 1-2 minutes, then check ticket status again:

```bash
curl http://localhost:8000/support/ticket/TICKET_ID
```

**Expected Result**:
- Ticket status: `resolved`
- Messages array includes AI response

### Test 4: Verify Database

```bash
psql $DATABASE_URL -c "SELECT id, status FROM tickets LIMIT 5;"
```

**Expected Result**:
- At least one ticket record

---

## Troubleshooting

### Issue: Redpanda won't start

**Symptoms**: Docker container exits immediately

**Solution**:
```bash
# Check if port 9092 is already in use
lsof -i :9092

# Stop conflicting service or change Redpanda port
docker run -d --name redpanda -p 9093:9092 ...
# Update KAFKA_BOOTSTRAP_SERVERS in .env to localhost:9093
```

---

### Issue: Database connection error

**Symptoms**: Backend logs show "connection refused" to Supabase

**Solution**:
1. Verify DATABASE_URL in .env is correct
2. Check Supabase project is active
3. Ensure your IP is whitelisted in Supabase dashboard
4. Test connection:
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

---

### Issue: AI API returns errors

**Symptoms**: Worker logs show 401 or 429 errors from OpenRouter

**Solution**:
1. Verify API key in .env is correct
2. Check API key has sufficient credits
3. Verify API endpoint URL
4. Test API directly:
   ```bash
   curl https://openrouter.ai/api/v1/chat/completions \
     -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "meta-llama/llama-3-8b-instruct:free", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

---

### Issue: WhatsApp webhook not receiving messages

**Symptoms**: No logs when sending WhatsApp messages

**Solution**:
1. Verify webhook URL is publicly accessible (use ngrok for local development)
   ```bash
   ngrok http 8000
   ```
2. Update webhook URL in Meta WhatsApp dashboard to `https://[ngrok-url]/webhooks/whatsapp`
3. Verify Meta WhatsApp credentials in .env are correct
4. Check X-Hub-Signature validation is disabled for testing or properly configured

---

### Issue: Worker not processing messages

**Symptoms**: Messages stay in `pending` status, worker logs show no activity

**Solution**:
1. Verify worker is connected to Redpanda:
   ```bash
   docker logs redpanda | grep "Connected"
   ```
2. Check Kafka topic exists:
   ```bash
   docker exec -it redpanda rpk topic list
   ```
3. Verify consumer group is subscribed:
   ```bash
   docker exec -it redpanda rpk group describe fte-message-processor
   ```
4. Restart worker with debug logging:
   ```bash
   LOG_LEVEL=DEBUG python backend/worker/message_processor.py
   ```

---

## Development Workflow

### Making Changes

1. **Backend changes**:
   - Edit files in `backend/`
   - FastAPI auto-reloads on save (dev mode)
   - Test at http://localhost:8000/docs

2. **Frontend changes**:
   - Edit files in `frontend/`
   - Next.js auto-reloads on save
   - Test at http://localhost:3000

3. **Worker changes**:
   - Edit files in `backend/worker/`
   - Restart worker process (Ctrl+C, then re-run)

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Viewing Logs

```bash
# Backend logs (if not using --reload)
# Check terminal where uvicorn is running

# Worker logs
# Check terminal where worker is running

# Redpanda logs
docker logs redpanda -f

# Frontend logs
# Check terminal where npm run dev is running
```

---

## Next Steps

After getting the system running:

1. **Customize Knowledge Base**: Edit `context/knowledge_base.json` with your product documentation
2. **Configure Escalation Rules**: Edit `context/escalation_rules.json`
3. **Test WhatsApp Integration**: Set up ngrok and configure Meta WhatsApp webhook
4. **Deploy to Production**: See deployment guide in `docs/deployment.md`

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│  FastAPI    │────▶│  Redpanda   │
│  (Port 3000)│     │  (Port 8000)│     │  (Port 9092)│
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Supabase   │◀────│   Worker    │◀────│  AI API     │
│  (External) │     │ (Background)│     │ (OpenRouter)│
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review logs for error messages
3. Consult API documentation: http://localhost:8000/docs
4. Check project README for additional guidance
