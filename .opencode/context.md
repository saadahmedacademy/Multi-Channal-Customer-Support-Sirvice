# AI Customer Support Agent

> Multi-channel AI-powered customer support with web form, WhatsApp, and email · Backend: FastAPI · Frontend: Next.js 16 · DB: PostgreSQL (Supabase) · AI: Hugging Face Inference

Scanned: 2026-07-08

## Architecture
User → Web Form / WhatsApp / Email → FastAPI → Async Queue → AI Agent → Response (↕ PostgreSQL via Supabase)

## Stack
| Layer | Tech |
|-------|------|
| Backend | Python 3.11 + FastAPI |
| Frontend | Next.js 16 + React 19 + Tailwind CSS 4 |
| Database | PostgreSQL (asyncpg) via Supabase |
| Queue | Redpanda / in-process async fallback (HF Spaces) |
| AI | Hugging Face Inference API |
| Email | Gmail API (OAuth2 + service account) |
| WhatsApp | Meta Cloud API webhook |

## Key Files
| Path | Role |
|------|------|
| backend/api/main.py | FastAPI app + lifespan + middleware + route registration |
| backend/api/routes/ | 9 route modules — conversations, customer_linking, customers, email, health, metrics, tickets, web_form, whatsapp |
| backend/config/settings.py | Pydantic settings (31 env vars via Field) |
| backend/db/connection.py | asyncpg pool manager |
| backend/db/repositories/ | 6 repos — conversation, customer, customer_identifier, knowledge, message, ticket |
| backend/integrations/ | 3 clients — email_client, queue_client, whatsapp_client |
| backend/worker/ | 5 modules — ai_agent, escalation, message_processor, sentiment, ticket_service |
| backend/hf_main.py | HF Spaces unified entry (app + worker + email sync, QUEUE_MODE=local) |
| backend/api/middleware/ | 4 middleware — error_handler, performance, rate_limiter, security_headers |
| frontend/src/app/ | Next.js App Router (6 page dirs — admin, customers, privacy, terms, ticket; api/ has sub-routes) |
| database/schema.sql | Full DDL (including pgvector) |
| .github/workflows/ | 4 workflows — build, security, sync-to-hub, test |

## Navigation Patterns
- **API routes**: Read `backend/api/routes/<name>.py` — each file has `@router.get/post/...` annotations.
- **Env vars**: Search `backend/config/settings.py` for `Field(...)` — 31 env vars with type + default.
- **DB schema**: See `database/schema.sql` for DDL; `backend/db/repositories/` for query patterns.
- **Frontend pages**: Each dir under `frontend/src/app/` is a route; `page.tsx` = page, `route.ts` = API, `layout.tsx` = layout.
- **Conventions**: Linter: PEP 8 (manual), Formatter: N/A, Test: pytest (asyncio_mode=auto), CSS: Tailwind CSS v4, Commit: descriptive.

## Conventions
- Raw SQL via asyncpg (no ORM for queries); SQLAlchemy + Alembic for migrations
- Input sanitization via bleach for user-generated content
- Exception handling via `register_exception_handlers` middleware
- Internal API routes require `X-API-Key` header (`internal_api_keys`)
- AI provider: Hugging Face Inference API (single provider)
- CI/CD via GitHub Actions (build, test, security scan, sync to HF Hub)

## Deploy Targets
| Target | URL |
|--------|-----|
| HF Spaces | Docker-based unified backend (hf_main.py) — saadi786/ai-customer-support |
| Vercel | https://multi-channal-customer-support-sirv.vercel.app |
