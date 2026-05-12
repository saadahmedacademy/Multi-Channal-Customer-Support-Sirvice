# AI Customer Support Agent (Digital FTE)

A lightweight, multi-channel AI customer support agent that receives customer messages via web form and WhatsApp, processes them asynchronously through a queue, generates AI-powered responses, and maintains conversation history across channels.

## Features

- 🌐 **Web Support Form**: Customers can submit support requests via a Next.js web form
- 💬 **WhatsApp Integration**: Meta WhatsApp Cloud API for messaging support
- 🤖 **AI-Powered Responses**: OpenRouter/Gemini AI for intelligent response generation
- 🔄 **Cross-Channel Continuity**: Unified conversation history across channels
- ⚡ **Async Processing**: Redpanda queue for reliable message processing
- 📊 **Ticket Tracking**: Unique ticket IDs with status tracking
- 🎯 **Smart Escalation**: Automatic escalation for pricing, refund, and legal queries

## Tech Stack

**Backend**:
- Python 3.11+ with FastAPI
- Redpanda (lightweight Kafka alternative)
- Supabase PostgreSQL with pgvector
- OpenRouter/Gemini AI APIs

**Frontend**:
- Next.js 14 with App Router
- React 18
- TypeScript

**Infrastructure**:
- Single-node deployment (4GB RAM optimized)
- Docker Compose for local development

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for Redpanda)
- Supabase account (free tier)
- OpenRouter API key

### 1. Clone and Setup

```bash
cd /home/saadahmed/hk-5

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Redpanda

```bash
docker run -d --name redpanda \
  -p 9092:9092 \
  docker.redpanda.com/redpandadata/redpanda:latest \
  redpanda start --smp 1 --memory 512M --overprovisioned
```

### 4. Setup Database

```bash
psql $DATABASE_URL -f database/schema.sql
```

### 5. Start Backend

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start Worker

```bash
python backend/worker/message_processor.py
```

### 7. Start Frontend

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000 to access the support form.

## Project Structure

```
project/
├── backend/
│   ├── api/              # FastAPI routes and schemas
│   ├── worker/           # Message processor and AI agent
│   ├── integrations/     # WhatsApp, queue clients
│   ├── db/               # Database models and repositories
│   └── config/           # Configuration and logging
├── frontend/
│   ├── app/              # Next.js pages and API routes
│   ├── components/       # React components
│   └── styles/           # CSS styles
├── context/              # Knowledge base and escalation rules
├── database/             # SQL schema and migrations
└── tests/                # Test suites
```

## API Endpoints

- `POST /support/submit` - Submit support request (web form)
- `GET /support/ticket/{id}` - Check ticket status
- `POST /webhooks/whatsapp` - WhatsApp webhook (Meta)
- `GET /health` - Health check
- `GET /metrics/channels` - Channel metrics

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Style

```bash
# Backend lint
cd backend
flake8 .
black .
isort .

# Frontend lint
cd frontend
npm run lint
```

## Deployment

See `docs/deployment.md` for production deployment guide.

## License

MIT

## Support

For issues or questions, please use the support form at http://localhost:3000
