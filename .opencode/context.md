# Project Context — AI Customer Support Agent

Scanned: 2026-06-13

## Architecture
FastAPI backend (asyncpg/PG) + Next.js 16 frontend + async worker consuming Redpanda/Kafka queue. Three channel inputs (web form, WhatsApp Meta API, Gmail API). AI responses via OpenRouter/Gemini/HuggingFace. Single-container HF Spaces deploys with local in-process queue.

## Stack
| Layer | Tech | Notes |
|-------|------|-------|
| Backend | Python 3.11 + FastAPI | asyncpg pool (5–20), pydantic-settings |
| Frontend | Next.js 16 + React 19 + TS | Tailwind CSS v4, standalone output |
| Database | PostgreSQL (Supabase) | asyncpg, pgBouncer-compat |
| Queue | Redpanda / local fallback | Topic: tickets_incoming, escalations |
| AI | OpenRouter → Gemini → HF | Model: meta-llama/llama-3.3-70b-instruct:free |
| Email | Gmail API (OAuth) | Pub/sub webhook + periodic sync |
| WhatsApp | Meta Cloud API | HMAC signature verification |

## Key Files
| Path | Purpose |
|------|---------|
| backend/api/main.py | FastAPI app, lifespan, CORS/middleware, router includes |
| backend/api/routes/ | 9 route modules (web_form, tickets, whatsapp, email, customers, customer_linking, conversations, metrics, health) |
| backend/config/settings.py | Pydantic settings (32 env vars) |
| backend/db/connection.py | asyncpg pool manager |
| backend/db/repositories/ | 5 repos (customer, conversation, ticket, customer_identifier, knowledge) |
| backend/integrations/ | email_client, queue_client, whatsapp_client |
| backend/worker/ | message_processor, ai_agent, escalation, sentiment, ticket_service |
| backend/hf_main.py | HF Spaces unified entry: app + worker + email sync |
| frontend/src/app/ | Next.js App Router pages + API routes |
| docker-compose.yml | 4 services: redpanda, backend, worker, frontend |
| Dockerfile | Single-container HF Spaces build |

## API Routes
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | / | — | API info |
| GET | /health | — | Health check |
| POST | /support/submit | — | Web form submission |
| GET | /support/ticket/{id} | — | Ticket status |
| GET | /webhooks/whatsapp | — | WA webhook verify |
| POST | /webhooks/whatsapp | — | WA webhook receive |
| POST | /webhooks/email | — | Email webhook receive |
| GET | /webhooks/email/test | — | Email test |
| POST | /webhooks/email/gmail/sync | — | Manual Gmail sync |
| GET | /customers/lookup | API key | Customer by email/phone |
| GET | /customers/{id}/conversations | — | Customer convos |
| POST | /customers/link-identifiers | — | Cross-channel linking |
| GET | /customers/{id}/identifiers | — | Linked identifiers |
| GET | /conversations/{id} | API key | Conversation + msgs |
| GET | /conversations/{id}/history | — | Last N messages |
| GET | /metrics/channels | API key | Per-channel metrics |
| GET | /metrics/tickets/summary | — | Ticket trend (N days) |
| GET | /health | — | Detailed component health |
| GET | /health/live | — | Liveness probe |
| GET | /health/ready | — | Readiness probe |

## Frontend Pages
| Route | Type | Description |
|-------|------|-------------|
| / | page + layout | Support form + ticket status |
| /ticket/[id] | page + error + loading | Ticket detail |
| /customers/link | page + error + loading | Link identifiers |
| /privacy | page | Privacy policy |
| /terms | page | Terms of service |
| /api/submit | route | Proxies POST /support/submit |
| /api/ticket/[ticketId] | route | Proxies GET /support/ticket/{id} |
| /api/health | route | Proxies GET /health |
| /api/customers/link-identifiers | route | Proxies POST /customers/link-identifiers |

## Environment Variables
| Var | Default | Secret? | Required? |
|-----|---------|---------|-----------|
| ENVIRONMENT | development | no | no |
| LOG_LEVEL | INFO | no | no |
| DATABASE_URL | None | **yes** | **yes** |
| SUPABASE_URL | None | no | no |
| SUPABASE_KEY | None | **yes** | no |
| OPENROUTER_API_KEY | None | **yes** | one of |
| GEMINI_API_KEY | None | **yes** | one of |
| HUGGINGFACE_API_KEY | None | **yes** | no |
| HUGGINGFACE_MODEL | meta-llama/Meta-Llama-3-8B-Instruct | no | no |
| META_WHATSAPP_TOKEN | None | **yes** | no |
| META_WHATSAPP_PHONE_ID | None | **yes** | no |
| META_WHATSAPP_BUSINESS_ID | None | **yes** | no |
| WHATSAPP_VERIFY_TOKEN | whatsapp-verify-token | no | no |
| WHATSAPP_APP_SECRET | None | **yes** | no |
| GMAIL_OAUTH_TOKEN | None | **yes** | no |
| GMAIL_REFRESH_TOKEN | None | **yes** | no |
| GMAIL_CLIENT_ID | None | **yes** | no |
| GMAIL_CLIENT_SECRET | None | **yes** | no |
| GMAIL_CREDENTIALS | None | **yes** | no |
| GMAIL_SERVICE_ACCOUNT_EMAIL | None | no | no |
| SUPPORT_EMAIL | None | no | no |
| KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | no | no |
| SECRET_KEY | (random) | **yes** | no |
| INTERNAL_API_KEYS | None | **yes** | no |
| CORS_ORIGINS | localhost:3000,vercel.app | no | no |
| RATE_LIMIT_REQUESTS | 100 | no | no |
| RATE_LIMIT_WINDOW | 60 (s) | no | no |
| AI_MODEL | meta-llama/llama-3.3-70b-instruct:free | no | no |
| AI_TIMEOUT | 30 | no | no |
| MAX_TOKENS | 500 | no | no |
| ESCALATION_SENTIMENT_THRESHOLD | 0.3 | no | no |

## Conventions
- Linter: ESLint (Next.js frontend)
- Test: pytest (asyncio_mode=auto, coverage, markers: unit/integration/api/e2e/slow)
- CSS: Tailwind CSS v4 + PostCSS
- Commit style: conventional-commits (fix:, feat:)
- Python: pydantic-settings for config, sanitize all user input (XSS prevention)
- DB: async with db.acquire(), raw SQL (no ORM)

## Deploy Targets
| Target | URL |
|--------|-----|
| HF Spaces | https://saadi786-ai-customer-support.hf.space |
| Vercel | https://multi-channal-customer-support-sirv.vercel.app |

## Last 5 Commits
- `e936be4` Remove unnecessary docs (stale session artifacts, duplicate deployment guides, outdated status reports)
- `516f33b` Cleanup: remove unnecessary files (reports, history, specs, scripts, dead code, duplicates), update gitignore, consolidate pytest/coverage config, rewrite READMEs
- `11b1350` Frontend improvements: scrollbar, toast system, ARIA tabs, Privacy/Terms pages, form state preservation, clipboard utility, API error handling, loading/error boundaries, phone validation, glassmorphism unification, beforeunload warning
- `72d15bb` fix: update support email to lasanitech7@gmail.com; prevent dark mode flash on load
- `dd8f606` feat: show 'Copied!' toast on message copy, 'Ticket ID copied!' on ticket copy
