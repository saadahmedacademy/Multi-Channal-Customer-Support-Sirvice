# Implementation Plan: Multi-Channel AI Customer Support Agent

**Branch**: `001-multi-channel` | **Date**: 2026-03-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification for multi-channel AI customer support with Web and WhatsApp intake

## Summary

Build a lightweight, multi-channel AI customer support agent that receives customer messages via web form and WhatsApp, processes them asynchronously through a queue, generates AI-powered responses, and maintains conversation history across channels. The system prioritizes simplicity and low-resource operation (4GB RAM) while delivering reliable 24/7 support automation.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/JavaScript (frontend)
**Primary Dependencies**: FastAPI, Next.js, Redpanda, Supabase PostgreSQL, OpenRouter/Gemini API
**Storage**: Supabase PostgreSQL with pgvector extension
**Testing**: pytest with async support (backend), Jest/React Testing Library (frontend)
**Target Platform**: Linux server (single-node deployment)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: <5 second confirmation time, <2 minute average response time, 99% uptime
**Constraints**: 4GB RAM max, single-node Redpanda, cloud AI APIs only, no Kubernetes
**Scale/Scope**: 2 channels (Web + WhatsApp), MVP focused on core support flow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Notes |
|------------------------|-------------------|-------|
| I. Low-Resource First (4GB RAM) | ✅ PASS | Single-node Redpanda, cloud AI APIs, lightweight FastAPI |
| II. Simplicity Over Scalability | ✅ PASS | No K8s, no heavy Docker, no microservices, no local LLMs |
| III. Async Event-Driven Architecture | ✅ PASS | All messages flow through Redpanda queue |
| IV. Modular Design | ✅ PASS | Separate API, worker, integrations directories |
| V. Build Incrementally | ✅ PASS | One spec at a time, P1 (Web) before P2 (WhatsApp) |
| VI. Graceful Failure Handling | ✅ PASS | Error handling and fallback responses planned |
| VII. AI Response Standards | ✅ PASS | Escalation rules for pricing/refund/anger |
| Forbidden Technologies | ✅ PASS | No K8s, no heavy Docker, no local LLMs, no complex microservices |
| Required Technologies | ✅ PASS | Next.js, FastAPI, Redpanda, Supabase, WhatsApp Cloud API |
| Project Structure | ✅ PASS | Follows prescribed directory layout |

**GATE RESULT**: ✅ All principles pass. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-multi-channel/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── api/
│   ├── main.py              # FastAPI application entry
│   ├── routes/
│   │   ├── web_form.py      # Web form submission endpoints
│   │   ├── whatsapp.py      # WhatsApp webhook endpoints
│   │   └── tickets.py       # Ticket status lookup endpoints
│   ├── middleware/
│   │   └── error_handler.py # Global error handling
│   └── schemas/
│       ├── tickets.py       # Pydantic schemas for tickets
│       └── messages.py      # Pydantic schemas for messages
├── worker/
│   ├── message_processor.py # Queue consumer and message handler
│   ├── ai_agent.py          # AI response generation
│   ├── escalation.py        # Escalation logic
│   └── sentiment.py         # Sentiment analysis
├── integrations/
│   ├── whatsapp_client.py   # WhatsApp Cloud API client
│   ├── email_client.py      # Gmail API client (optional)
│   └── queue_client.py      # Redpanda/Kafka client
├── db/
│   ├── connection.py        # Database connection management
│   ├── repositories/
│   │   ├── customer_repo.py # Customer data access
│   │   ├── ticket_repo.py   # Ticket data access
│   │   └── conversation_repo.py # Conversation data access
│   └── models/
│       ├── customer.py      # Customer ORM model
│       ├── ticket.py        # Ticket ORM model
│       ├── conversation.py  # Conversation ORM model
│       └── message.py       # Message ORM model
└── config/
    ├── settings.py          # Environment configuration
    └── logging.py           # Logging configuration

frontend/
├── app/
│   ├── page.tsx             # Home page with support form
│   ├── components/
│   │   ├── SupportForm.tsx  # Support form component
│   │   ├── TicketStatus.tsx # Ticket status checker
│   │   └── ui/              # Reusable UI components
│   └── api/                 # API routes (Next.js)
│       └── submit.ts        # Form submission handler
├── public/
│   └── assets/              # Static assets
└── styles/
    └── globals.css          # Global styles

context/
├── knowledge_base.json      # Product documentation and FAQs
└── escalation_rules.json    # Escalation trigger definitions

database/
├── schema.sql               # PostgreSQL schema
├── migrations/              # Database migrations
└── seed.sql                 # Seed data for testing

tests/
├── contract/                # API contract tests
├── integration/             # Integration tests (queue → worker → AI)
└── unit/                    # Unit tests for individual modules
```

**Structure Decision**: Web application structure (Option 2) selected. Backend is a FastAPI application with separate API routes, worker processes, and integration handlers. Frontend is a Next.js application providing the support form UI. This structure aligns with constitution Principle IV (Modular Design) and supports the prescribed data flow standard.

## Complexity Tracking

> **No violations detected** - All constitution principles pass without requiring complexity justification.
