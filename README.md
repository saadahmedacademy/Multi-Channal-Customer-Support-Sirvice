---
title: AI Support Backend
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# AI Customer Support Agent

Multi-channel AI-powered customer support system with web form, WhatsApp, and email channels. Backend deployed on Hugging Face Spaces, frontend on Vercel.

## Architecture

```
User → Web Form / WhatsApp / Email → FastAPI → Async Queue → AI Agent → Response
                                              ↕
                                         PostgreSQL
                                       (Supabase)
```

- **Backend**: Python FastAPI with async message processing
- **Frontend**: Next.js 16 with App Router (Vercel)
- **Database**: Supabase PostgreSQL
- **AI**: Hugging Face Inference API
- **Queue**: In-process async queue (HF Spaces) / Redpanda (local dev)
- **Email**: Gmail API with OAuth 2.0 + label-based sync
- **WhatsApp**: Meta Cloud API webhook

## Quick Start

```bash
git clone <repo>
cd hk-5

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install && cd ..

# Configure
cp .env.example .env   # Fill in your API keys

# Start backend
cd backend && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (another terminal)
cd frontend && npm run dev
```

## Project Structure

```
├── backend/
│   ├── api/              # FastAPI routes & schemas
│   ├── worker/           # Message processor & AI agent
│   ├── integrations/     # Gmail, WhatsApp, queue clients
│   ├── db/               # Database models & repositories
│   └── config/           # Settings & logging
├── frontend/
│   ├── src/app/          # Next.js pages & API routes
│   ├── src/components/   # React components
│   └── src/lib/          # Shared utilities
├── database/             # SQL schema & Alembic migrations
├── context/              # Knowledge base & escalation rules
├── tests/                # Backend test suite
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

## Deployment

- **Backend**: Auto-deployed to Hugging Face Spaces via GitHub Actions (`sync-to-hub.yml`)
- **Frontend**: Auto-deployed to Vercel from `frontend/` directory
- **HF Space**: `saadi786/ai-customer-support` — single Docker container with in-process queue

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection string |
| `HUGGINGFACE_API_KEY` | Yes | Hugging Face API key for AI |
| `HUGGINGFACE_MODEL` | No | Hugging Face model ID (default: NousResearch/Hermes-3-Llama-3.1-8B) |
| `GMAIL_CLIENT_ID` | For email | Google OAuth client ID |
| `GMAIL_CLIENT_SECRET` | For email | Google OAuth client secret |
| `GMAIL_REFRESH_TOKEN` | For email | OAuth refresh token |
| `GMAIL_OAUTH_TOKEN` | For email | OAuth access token |
| `SUPPORT_EMAIL` | For email | Gmail address for support |
| `GMAIL_SYNC_LABEL` | For email | Gmail label for filtering support emails |
| `META_WHATSAPP_TOKEN` | For WhatsApp | Meta Cloud API access token |
| `QUEUE_MODE` | No | `local` (in-process) or `kafka` (Redpanda) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/support/submit` | Submit support request (web form) |
| GET | `/support/ticket/{id}` | Get ticket status & conversation |
| POST | `/webhooks/whatsapp` | WhatsApp webhook |
| POST | `/customers/link-identifiers` | Link customer identifiers across channels |
| GET | `/metrics/channels` | Channel usage metrics |

## Email Sync

Emails are synced every 30s (configurable via `EMAIL_SYNC_INTERVAL`). Only emails with the configured Gmail label (`GMAIL_SYNC_LABEL`, default: `SupportTicket`) are processed. Set `DISABLE_EMAIL_SYNC=1` to disable.

## License

MIT
