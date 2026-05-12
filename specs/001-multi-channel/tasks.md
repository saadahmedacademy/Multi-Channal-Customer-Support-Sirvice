# Tasks: Multi-Channel AI Customer Support Agent

**Input**: Design documents from `/specs/001-multi-channel/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Tests are OPTIONAL and NOT included in this task list. Add test tasks separately if TDD approach is requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/` at repository root (FastAPI application)
- **Frontend**: `frontend/` at repository root (Next.js application)
- **Database**: `database/` at repository root (PostgreSQL schema)
- **Context**: `context/` at repository root (knowledge base)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend directory structure: `backend/api/`, `backend/worker/`, `backend/integrations/`, `backend/db/`, `backend/config/`
- [x] T002 Create frontend directory structure: `frontend/app/`, `frontend/components/`, `frontend/styles/`
- [x] T003 Create shared directories: `database/`, `context/`, `tests/`
- [x] T004 [P] Initialize Python project with `backend/requirements.txt` (FastAPI, uvicorn, asyncpg, aiokafka, pydantic, python-dotenv)
- [x] T005 [P] Initialize Node.js project with `frontend/package.json` (Next.js, React, TypeScript)
- [x] T006 [P] Create `.env.example` with all required environment variables (DATABASE_URL, OPENROUTER_API_KEY, META_WHATSAPP_TOKEN, KAFKA_BOOTSTRAP_SERVERS)
- [x] T007 [P] Create `.gitignore` for Python and Node.js projects
- [x] T008 Create `README.md` with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 [P] Create database schema in `database/schema.sql` (customers, customer_identifiers, conversations, messages, tickets, knowledge_base tables)
- [x] T010 [P] Create database connection manager in `backend/db/connection.py` (asyncpg pool with 10 connections max)
- [x] T011 [P] Create database models in `backend/db/models/`: `customer.py`, `conversation.py`, `message.py`, `ticket.py`
- [x] T012 [P] Create repository layer in `backend/db/repositories/`: `customer_repo.py`, `ticket_repo.py`, `conversation_repo.py`
- [x] T013 [P] Create Redpanda queue client in `backend/integrations/queue_client.py` (aiokafka producer/consumer)
- [x] T014 [P] Create FastAPI application entry in `backend/api/main.py` with health endpoint
- [x] T015 [P] Create environment configuration in `backend/config/settings.py` (pydantic settings with validation)
- [x] T016 [P] Create logging configuration in `backend/config/logging.py` (structured JSON logging)
- [x] T017 [P] Create global error handler in `backend/api/middleware/error_handler.py`
- [x] T018 [P] Create Docker Compose file for Redpanda: `docker-compose.redpanda.yml`
- [x] T019 Create database migration script: `database/migrations/001_initial_schema.sql`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Web Support Form Submission (Priority: P1) 🎯 MVP

**Goal**: Customers can submit support requests via web form and receive AI-generated responses with ticket tracking

**Independent Test**: Submit web form → Verify ticket created → Verify AI response generated → Verify response stored in database

### Implementation for User Story 1

- [x] T020 [P] [US1] Create Pydantic schemas in `backend/api/schemas/tickets.py`: `SupportFormSubmission`, `SupportFormResponse`, `TicketStatusResponse`
- [x] T021 [P] [US1] Create Pydantic schemas in `backend/api/schemas/messages.py`: `MessageSchema`, `ConversationSchema`
- [x] T022 [US1] Implement web form POST endpoint in `backend/api/routes/web_form.py` (`/support/submit`)
- [x] T023 [US1] Implement ticket status GET endpoint in `backend/api/routes/tickets.py` (`/support/ticket/{ticket_id}`)
- [x] T024 [US1] Create ticket service in `backend/worker/ticket_service.py` (ticket creation, status updates)
- [x] T025 [US1] Create AI agent in `backend/worker/ai_agent.py` (OpenRouter API integration, response generation)
- [x] T026 [US1] Create escalation logic in `backend/worker/escalation.py` (pricing/refund/legal keyword detection)
- [x] T027 [US1] Create message processor worker in `backend/worker/message_processor.py` (Redpanda consumer, end-to-end flow)
- [x] T028 [P] [US1] Create Next.js support form component in `frontend/components/SupportForm.tsx`
- [x] T029 [P] [US1] Create Next.js ticket status component in `frontend/components/TicketStatus.tsx`
- [x] T030 [US1] Create Next.js home page in `frontend/app/page.tsx` with embedded support form
- [x] T031 [US1] Create Next.js API route in `frontend/app/api/submit.ts` for form submission
- [x] T032 [US1] Create knowledge base seed data in `context/knowledge_base.json` (10+ sample Q&A entries)
- [x] T033 [US1] Create escalation rules config in `context/escalation_rules.json` (keywords, sentiment thresholds)
- [x] T034 [US1] Add input validation to web form endpoint in `backend/api/routes/web_form.py` (field length, email format, required fields)
- [x] T035 [US1] Add channel-aware response formatting in `backend/worker/ai_agent.py` (formal tone for web form)
- [x] T036 [US1] Add database logging for all ticket operations in `backend/db/repositories/ticket_repo.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently
- Web form accessible at http://localhost:3000
- Form submission creates ticket and queues message
- Worker processes message and generates AI response
- Ticket status viewable via API

---

## Phase 4: User Story 2 - WhatsApp Message Support (Priority: P2)

**Goal**: Customers can send/receive WhatsApp messages with AI-powered support responses

**Independent Test**: Send WhatsApp message → Verify webhook received → Verify AI response generated → Verify response sent back to WhatsApp

### Implementation for User Story 2

- [x] T037 [P] [US2] Create Meta WhatsApp client in `backend/integrations/whatsapp_client.py` (Graph API integration for sending messages)
- [x] T038 [P] [US2] Create WhatsApp webhook endpoint in `backend/api/routes/whatsapp.py` (`/webhooks/whatsapp` POST)
- [x] T039 [P] [US2] Create WhatsApp status callback in `backend/api/routes/whatsapp.py` (`/webhooks/whatsapp/status` POST)
- [x] T040 [US2] Add X-Hub-Signature-256 validation in `backend/api/routes/whatsapp.py` (webhook security)
- [x] T041 [US2] Implement WhatsApp message parsing in `backend/worker/message_processor.py` (extract phone, message body from Meta webhook JSON)
- [x] T042 [US2] Add phone number normalization in `backend/db/repositories/customer_repo.py` (E.164 format)
- [x] T043 [US2] Add channel-aware response formatting in `backend/worker/ai_agent.py` (concise, conversational tone for WhatsApp, max 300 chars)
- [x] T044 [US2] Implement WhatsApp message sending in `backend/integrations/whatsapp_client.py` (Graph API POST request)
- [x] T045 [US2] Add delivery status tracking in `backend/db/repositories/message_repo.py` (update delivery_status field)
- [x] T046 [US2] Add rate limiting for WhatsApp messages in `backend/integrations/whatsapp_client.py` (1000 messages per 24h window)
- [x] T047 [US2] Add explicit escalation keywords for WhatsApp in `context/escalation_rules.json` ("human", "agent", "representative")
- [x] T048 [US2] Update health endpoint in `backend/api/main.py` to report WhatsApp channel status

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently
- Web form fully functional (from Phase 3)
- WhatsApp webhook receives messages
- AI generates conversational responses
- Responses sent back via WhatsApp Cloud API

---

## Phase 5: User Story 3 - Cross-Channel Conversation Continuity (Priority: P3)

**Goal**: Customers are recognized across channels with unified conversation history

**Independent Test**: Submit web form with email → Send WhatsApp from same phone/email → Verify AI references previous web form conversation

### Implementation for User Story 3

- [x] T049 [P] [US3] Create customer identifier repository in `backend/db/repositories/customer_identifier_repo.py` (link email/phone to customer)
- [x] T050 [US3] Implement customer resolution logic in `backend/worker/message_processor.py` (find customer by email or phone, merge identifiers)
- [x] T051 [US3] Add conversation history loading in `backend/db/repositories/conversation_repo.py` (get last 10 messages across all channels)
- [x] T052 [US3] Implement conversation continuity in `backend/worker/ai_agent.py` (include conversation history in AI context)
- [x] T053 [US3] Add cross-channel acknowledgment in `backend/worker/ai_agent.py` ("I see you contacted us previously about...")
- [x] T054 [US3] Implement conversation thread reuse in `backend/worker/ticket_service.py` (reuse active conversation within 24 hours)
- [x] T055 [US3] Add customer lookup endpoint in `backend/api/routes/customers.py` (`/customers/lookup?email=...&phone=...`)
- [x] T056 [US3] Add conversation history endpoint in `backend/api/routes/conversations.py` (`/conversations/{conversation_id}`)
- [x] T057 [US3] Update customer creation in `backend/db/repositories/customer_repo.py` (link multiple identifiers to single customer)
- [x] T058 [US3] Add duplicate detection in `backend/worker/ticket_service.py` (prevent duplicate tickets within 5 minutes)

**Checkpoint**: All user stories should now be independently functional
- Web form submissions work (US1)
- WhatsApp messages work (US2)
- Same customer recognized across channels (US3)
- Conversation history unified across channels

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T059 [P] Create channel metrics endpoint in `backend/api/routes/metrics.py` (`/metrics/channels`)
- [x] T060 [P] Add sentiment analysis in `backend/worker/sentiment.py` (keyword-based or API-based sentiment scoring)
- [x] T061 [P] Add metrics publishing in `backend/worker/message_processor.py` (publish to `metrics` topic)
- [x] T062 Create seed script for knowledge base: `database/seed.sql` (sample Q&A data)
- [x] T063 [P] Add CORS middleware in `backend/api/main.py` (allow frontend origin)
- [x] T064 [P] Add rate limiting middleware in `backend/api/middleware/rate_limiter.py` (10 submissions/minute per IP)
- [x] T065 Create quickstart validation script: `scripts/validate-setup.sh` (check all services running)
- [x] T066 [P] Add graceful shutdown handling in `backend/worker/message_processor.py` (SIGTERM handler)
- [x] T067 [P] Add health check improvements in `backend/api/main.py` (database, queue, AI API connectivity checks)
- [x] T068 Update documentation in `README.md` with deployment instructions
- [x] T069 Create `.env` file with actual values for local development
- [x] T070 Test full end-to-end flow: Web form → Queue → Worker → AI → Response → Database

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Builds on US1 and US2 customer identification

### Within Each User Story

- Models before services
- Services before endpoints
- Backend before frontend (for API contracts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T004, T005, T006, T007 can all run in parallel (different files)

**Phase 2 (Foundational)**:
- T009, T010, T011, T012, T013, T014, T015, T016, T017, T018 can all run in parallel (different files, no dependencies)

**Phase 3 (US1)**:
- T020, T021 (schemas) can run in parallel
- T028, T029 (frontend components) can run in parallel
- After schemas: T022, T023, T024, T025, T026, T027 can proceed in parallel
- Frontend (T028-T031) can proceed once backend API contracts are defined

**Phase 4 (US2)**:
- T037, T038, T039 (WhatsApp client and webhooks) can run in parallel
- After client/webhooks: T040-T048 can proceed based on availability

**Phase 5 (US3)**:
- T049 (customer identifier repo) can run in parallel with other foundational tasks
- T050-T058 depend on customer resolution logic being in place

**Phase 6 (Polish)**:
- T059, T060, T061, T063, T064, T066, T067 can all run in parallel

---

## Parallel Execution Examples

### Example 1: Foundational Phase (Maximum Parallelism)

```bash
# Launch all foundational tasks together:
Task: "Create database schema in database/schema.sql"
Task: "Create database connection manager in backend/db/connection.py"
Task: "Create database models in backend/db/models/"
Task: "Create repository layer in backend/db/repositories/"
Task: "Create Redpanda queue client in backend/integrations/queue_client.py"
Task: "Create FastAPI application in backend/api/main.py"
Task: "Create environment configuration in backend/config/settings.py"
Task: "Create logging configuration in backend/config/logging.py"
Task: "Create error handler in backend/api/middleware/error_handler.py"
Task: "Create Docker Compose for Redpanda"
```

### Example 2: User Story 1 (Backend/Frontend Parallelism)

```bash
# Backend team (or developer A):
Task: "Create Pydantic schemas in backend/api/schemas/"
Task: "Implement web form endpoint in backend/api/routes/web_form.py"
Task: "Create ticket service in backend/worker/ticket_service.py"
Task: "Create AI agent in backend/worker/ai_agent.py"
Task: "Create message processor in backend/worker/message_processor.py"

# Frontend team (or developer B) - after backend schemas defined:
Task: "Create SupportForm component in frontend/components/SupportForm.tsx"
Task: "Create TicketStatus component in frontend/components/TicketStatus.tsx"
Task: "Create home page in frontend/app/page.tsx"
Task: "Create API route in frontend/app/api/submit.ts"
```

### Example 3: User Story 2 (WhatsApp Integration)

```bash
# Launch WhatsApp integration tasks together:
Task: "Create WhatsApp client in backend/integrations/whatsapp_client.py"
Task: "Create WhatsApp webhook in backend/api/routes/whatsapp.py"
Task: "Create WhatsApp status callback in backend/api/routes/whatsapp.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete **Phase 1: Setup** (30 minutes)
2. Complete **Phase 2: Foundational** (2 hours)
3. Complete **Phase 3: User Story 1** (4-6 hours)
4. **STOP and VALIDATE**: Test web form end-to-end
5. Deploy/demo if ready

**MVP Scope**:
- Web form submission (T022, T028-T031)
- Basic ticket creation (T024)
- Simple AI response without escalation (T025, skip T026)
- Message processor (T027)
- Knowledge base with 5-10 entries (T032)

### Incremental Delivery

1. **Setup + Foundational** → Foundation ready
2. Add **User Story 1** → Test independently → Deploy/Demo (MVP!)
3. Add **User Story 2** → Test independently → Deploy/Demo
4. Add **User Story 3** → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With 2-3 developers:

**Developer A (Backend)**:
- Phase 2: Foundational (database, models, repositories)
- Phase 3: US1 backend (API, worker, AI agent)
- Phase 4: US2 backend (WhatsApp integration)

**Developer B (Frontend)**:
- Phase 1: Setup (frontend structure)
- Phase 3: US1 frontend (support form, ticket status)
- Phase 6: Polish (metrics UI if needed)

**Developer C (Full-stack/DevOps)**:
- Phase 1: Setup (backend structure, Docker)
- Phase 2: Foundational (queue, configuration)
- Phase 3: US1 integration (message processor)
- Phase 4: US2 webhooks
- Phase 5: US3 cross-channel logic

---

## Task Count Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 8 tasks |
| Phase 2 | Foundational | 11 tasks |
| Phase 3 | User Story 1 (Web Form) | 17 tasks |
| Phase 4 | User Story 2 (WhatsApp) | 12 tasks |
| Phase 5 | User Story 3 (Cross-Channel) | 10 tasks |
| Phase 6 | Polish & Cross-Cutting | 12 tasks |
| **Total** | **All phases** | **70 tasks** |

**Parallel Opportunities**: 35 tasks marked with [P] can run in parallel

**MVP Minimum**: ~25 tasks (Phase 1 + Phase 2 + US1 core tasks)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [US1], [US2], [US3] labels map tasks to specific user stories for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group of tasks
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Frontend tasks can only start after backend API contracts (schemas) are defined
