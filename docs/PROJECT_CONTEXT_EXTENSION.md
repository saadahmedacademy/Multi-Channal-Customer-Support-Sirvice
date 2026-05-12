# Project Context Extension (AI Customer Support Agent)

This document serves as an extension to `AGENTS.md` and provides deeper context for the AI Customer Support Agent (Digital FTE) project. Due to length constraints in `AGENTS.md`, this file maintains the expanded architectural, historical, and functional context necessary for development.

## 1. Project Overview & Architecture

The system is a lightweight, multi-channel AI customer support agent. It ingests messages from various channels, queues them for reliable processing, generates responses using LLMs, and maintains a unified cross-channel conversation history.

### Core Workflow
1. **Ingestion**: Messages arrive via web form (`POST /support/submit`), WhatsApp Webhook (`POST /webhooks/whatsapp`), or Gmail (fetched via script and forwarded).
2. **API/Queueing**: The FastAPI backend validates payloads and publishes events to Redpanda topics.
3. **Processing**: The Python worker (`worker/message_processor.py`) consumes Redpanda messages, retrieves conversation history from Supabase (PostgreSQL), and invokes the OpenRouter/Gemini API to generate context-aware responses.
4. **Delivery/Persistence**: Responses are sent back to the respective channels, and the full interaction is saved in the database to maintain history and ticket tracking.

## 2. Recent Additions: Gmail Integration

The project has recently been extended to support Gmail as a customer support channel. This allows the system to read incoming emails and treat them as support tickets.

### Components
- **`scripts/get_gmail_token.py`**: A utility script to perform the OAuth2 flow with Google. It generates and saves the necessary `credentials.json` (or token files) required for API access.
- **`scripts/fetch_gmail_emails.py`**: A recurring script that connects to the Gmail API, fetches unread emails, parses their content, and forwards them to the backend (acting effectively as a webhook for email).
- **Environment Updates**: `.env` requires Gmail API credentials (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, etc.) for the integration to function.

## 3. The Agent Ecosystem

The repository uses AI agents for development and operational tasks:

- **Agent Configuration (`AGENTS.md`)**: Primary agent setup focused on architectural planning, spec-driven development, and direct codebase manipulation.

*Note: Check `AGENTS.md` for specific rules regarding how agents should operate within the workspace.*

## 4. Development & Deployment Nuances

- **Database**: Supabase PostgreSQL is used, leveraging `pgvector` for potential semantic search/RAG capabilities within the knowledge base.
- **Redpanda**: Used as a lightweight Kafka alternative. Ensure Docker is running and Redpanda is started before testing the worker process.
- **Frontend**: Next.js 14 App Router application (`frontend/`). Requires its own `.env` configuration (typically pointing to the backend API).
- **Testing**:
  - Backend: Run `pytest` in the `backend/` directory.
  - Frontend: Run `npm test` in the `frontend/` directory.
  - Test suites are critical for validating new channels (like Gmail) and ensuring existing flows (WhatsApp, Web) do not break.

## 5. Maintenance Checklist for Agents
When working on this project, ensure you:
1. Verify the `.env` variables if working on integration components (WhatsApp, Gmail, OpenRouter).
2. Start both the FastAPI server (`uvicorn`) and the Worker (`python backend/worker/message_processor.py`) when testing end-to-end flows.
3. Keep the frontend up-to-date if adding new ticket tracking features.
4. Always consult this document and `AGENTS.md` before proposing large architectural changes.
