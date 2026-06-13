# AI Customer Support Agent

> Multi-channel AI-powered customer support with web form, WhatsApp, and email · Backend: Python 3.11 + FastAPI · Frontend: Next.js 16 + React 19 · DB: PostgreSQL (Supabase) · AI: OpenRouter → Gemini → HF Inference

Scanned: 2026-06-13

## Architecture
User → Web Form / WhatsApp / Email → FastAPI → Async Queue → AI Agent → Response. State persisted in PostgreSQL (Supabase). Unified Docker entry point on HF Spaces with in-process queue fallback.

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
| backend/api/main.py | FastAPI app + lifespan + middleware + 8 route groups |
| backend/api/routes/ | 9 modules — web_form, tickets, whatsapp, email, customers, customer_linking, conversations, metrics, health |
| backend/config/settings.py | Pydantic Settings (31 env vars via `Field(...)`) |
| backend/db/connection.py | asyncpg pool manager |
| backend/db/repositories/ | 5 repos — conversation, customer_identifier, customer, knowledge, ticket |
| backend/integrations/ | email_client, queue_client, whatsapp_client |
| backend/worker/ | ai_agent, escalation, message_processor, sentiment, ticket_service |
| backend/hf_main.py | HF Spaces unified entry (app + worker + email sync) |
| frontend/src/app/ | Next.js App Router (5 page dirs + API routes) |
| .github/workflows/ | build, security, sync-to-hub, test |

## Navigation Patterns
- **API routes**: Read `backend/api/routes/<name>.py` — each file has its own `@router.get/post/...` annotations.
- **Env vars**: Search `Field(...)` in `backend/config/settings.py` — 31 fields with defaults and types.
- **DB schema**: See `database/schema.sql` for full DDL, or `backend/db/repositories/` for query patterns.
- **Frontend pages**: Each dir under `frontend/src/app/` is a route; `page.tsx` = page, `route.ts` = API, `layout.tsx` = layout.
- **Conventions**: Linter=eslint · Test=`pytest --cov` · CSS=Tailwind CSS 4 · Commit=conventional.

## Conventions
- pytest (asyncio_mode=auto) · eslint · Tailwind CSS 4 · conventional commits
- Raw SQL via asyncpg (no ORM); Pydantic v2 for validation; rate limiting via middleware

## Deploy Targets
| Target | URL |
|--------|-----|
| HF Spaces | saadi786/ai-customer-support |
| Vercel | multi-channal-customer-support-sirv.vercel.app |
