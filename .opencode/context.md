# AI Customer Support Agent

> Multi-channel AI-powered customer support with web form, WhatsApp, and email · Backend: Python 3.11 + FastAPI · Frontend: Next.js 16 + React 19 + Tailwind CSS 4 · DB: PostgreSQL (Supabase) · AI: OpenRouter → Gemini → HF Inference

Scanned: 2026-06-20

## Architecture
User → Web Form / WhatsApp / Email → FastAPI → Async Queue (Redpanda/fallback) → AI Agent → Response. State in PostgreSQL (Supabase). Unified Docker entry on HF Spaces. Per-message feedback + multi-turn chat on web frontend.

## Stack
| Layer | Tech |
|-------|------|
| Backend | Python 3.11 + FastAPI |
| Frontend | Next.js 16 + React 19 + Tailwind CSS 4 |
| Database | PostgreSQL (Supabase, asyncpg) |
| Queue | Redpanda / local in-process fallback |
| AI | OpenRouter → Gemini → Hugging Face Inference |
| Email | Gmail API (OAuth2) |
| WhatsApp | Meta Cloud API |

## Key Files
| Path | Role |
|------|------|
| `backend/api/main.py` | FastAPI app + lifespan + 4 middleware + 8 route groups + health |
| `backend/api/routes/` | 8 modules — conversations, customer_linking, customers, email, health, metrics, tickets, web_form, whatsapp |
| `backend/api/middleware/` | 4 modules — error_handler, performance, rate_limiter, security_headers |
| `backend/config/settings.py` | Pydantic Settings (31 env vars via `Field(...)`) |
| `backend/db/connection.py` | asyncpg pool manager |
| `backend/db/repositories/` | 6 repos — conversation, customer_identifier, customer, knowledge, message, ticket |
| `backend/integrations/` | email_client, queue_client, whatsapp_client |
| `backend/worker/` | ai_agent, escalation, message_processor, sentiment, ticket_service |
| `backend/hf_main.py` | HF Spaces unified entry (app + worker + email sync) |
| `frontend/src/app/` | Next.js App Router (5 pages — /, /customers, /privacy, /terms, /ticket + 6 API routes) |
| `.github/workflows/` | build, security, sync-to-hub, test |

## Navigation Patterns
- **API routes**: Read `backend/api/routes/<name>.py` — each file has its own `@router.get/post/...`. Prefixes: `/support` (web_form, tickets), `/webhooks` (whatsapp, email), `/customers` (customers, customer_linking), `/conversations` (conversations), `/metrics` (metrics), `/health` (built-in).
- **Env vars**: Search `Field(...)` in `backend/config/settings.py` — 31 fields with defaults and types.
- **DB schema**: See `database/schema.sql` for full DDL, or `backend/db/repositories/` for query patterns.
- **Frontend pages**: Each dir under `frontend/src/app/` is a route; `page.tsx` = page, `route.ts` = API, `layout.tsx` = layout.
- **Frontend API proxies**: Under `frontend/src/app/api/` — proxy routes forward to backend; naming mirrors backend paths.
- **Feedback/multi-turn**: `POST /conversations/{id}/messages` for follow-up; `POST /conversations/messages/{id}/feedback` for thumbs up/down. See `message_repo.py` for DB queries.

## Conventions
- pytest (asyncio_mode=auto, --cov=backend) · eslint (Next.js) · Tailwind CSS 4 · conventional commits
- Raw SQL via asyncpg (no ORM); Pydantic v2 for validation; rate limiting + security headers via middleware
- Each web form submission creates a fresh session; no conversation reuse across submissions

## Deploy Targets
| Target | URL |
|--------|-----|
| HF Spaces | saadi786/ai-customer-support |
| Vercel | multi-channal-customer-support-sirv.vercel.app |
