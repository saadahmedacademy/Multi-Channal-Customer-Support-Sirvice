# AI Customer Support Agent - Documentation

**Multi-Channel AI Customer Support System (Digital FTE)**  
**Status**: Production Ready | **Tech**: Python/FastAPI, Next.js, PostgreSQL, Redpanda

---

## 📋 Quick Start

**Main Docs**: [README.md](README.md) | **Recent Changes**: [Implementation Summary](docs/IMPLEMENTATION.md) | **Deploy**: [Deployment Runbook](docs/DEPLOYMENT_RUNBOOK.md)

### Setup
```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
alembic upgrade head
python scripts/seed_knowledge_base.py

# Services
uvicorn backend.api.main:app --reload --port 8000
python backend/worker/message_processor.py

# Frontend
cd frontend && npm install && npm run dev
```

---

## 📚 Documentation

### Architecture & Design
- [Project Brief](docs/PROJECT_BRIEF.md) - Original requirements
- [Project Context](docs/PROJECT_CONTEXT_EXTENSION.md) - Architecture details
- [Implementation Summary](docs/IMPLEMENTATION.md) - Completed improvements
- [Agent Configuration](docs/AGENTS.md) - AI agent setup

### Specifications
- [Multi-Channel Spec](specs/001-multi-channel/spec.md) - Feature specification
- [Data Model](specs/001-multi-channel/data-model.md) - Database schema
- [API Contracts](specs/001-multi-channel/contracts/api-contracts.md) - Endpoints
- [Implementation Plan](specs/001-multi-channel/plan.md) - Development plan
- [Task Breakdown](specs/001-multi-channel/tasks.md) - Task list

### Setup Guides
- [Email Setup](docs/EMAIL_SETUP_GUIDE.md) - Gmail integration
- [Hugging Face Setup](docs/HUGGINGFACE_SETUP.md) - HF API configuration
- [Database Migrations](docs/DATABASE_MIGRATIONS.md) - Alembic workflow
- [Frontend Guide](docs/FRONTEND_README.md) - Next.js structure

### Security
- [Security Incident](docs/SECURITY_INCIDENT.md) - OAuth credential exposure remediation
- [RLS Security Fix](docs/RLS_SECURITY_FIX.md) - Row-Level Security vulnerability fix

---

## 🏗️ Project Structure

```
backend/          # FastAPI backend
  api/           # Routes, schemas, middleware
  worker/        # Message processor, AI agent
  integrations/  # WhatsApp, Email, Queue clients
  db/            # Database repositories
  utils/         # Security, authentication
frontend/        # Next.js frontend
  src/app/       # Pages and API routes
  src/components/# React components
database/        # Schema and migrations
context/         # Knowledge base, escalation rules
docs/            # All documentation
scripts/         # Utility scripts
tests/           # Unit, integration, API tests
specs/           # Feature specifications
```

---

## 🔐 Security & Configuration

### Authentication
- **Internal APIs**: Require `X-API-Key` header
- **Protected**: `/customers/*`, `/conversations/*`, `/metrics/*`
- **Config**: `INTERNAL_API_KEYS` in `.env`

### Key Environment Variables
```bash
DATABASE_URL=postgresql://...
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=...
HUGGINGFACE_API_KEY=hf_...
OPENAI_API_KEY=sk-...  # Optional, for embeddings
META_WHATSAPP_TOKEN=...
GMAIL_OAUTH_TOKEN=...
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
INTERNAL_API_KEYS=...
SECRET_KEY=...
BACKEND_URL=http://localhost:8000
```

See `.env.example` for complete list.

---

## 📡 API Endpoints

### Public
- `POST /support/submit` - Submit support request
- `GET /support/ticket/{id}` - Check ticket status
- `POST /webhooks/whatsapp` - WhatsApp webhook
- `POST /webhooks/email` - Email webhook
- `GET /health` - Health check

### Internal (Require API Key)
- `GET /customers/lookup` - Customer lookup
- `GET /conversations/{id}` - Conversation history
- `GET /metrics/channels` - Channel metrics

**Interactive Docs**: `http://localhost:8000/docs`

---

## 🧪 Testing

```bash
pytest                              # All tests
pytest --cov=backend --cov-report=html  # With coverage
pytest tests/unit/test_worker.py   # Specific test
```

**Reports**: [Final Summary](test-results/FINAL_SUMMARY.md) | [Detailed Report](test-results/TEST_REPORT.md)

---

## 🚀 Deployment

**Full Guide**: [Deployment Runbook](docs/DEPLOYMENT_RUNBOOK.md)

### Quick Deploy
1. Install: `pip install -r backend/requirements.txt`
2. Migrate: `alembic upgrade head`
3. Seed: `python scripts/seed_knowledge_base.py`
4. Configure: Update `.env` with required variables
5. Start: API, Worker, Frontend services

---

## 🔍 Troubleshooting

**Health check fails**: Check database and Redpanda connections  
**Form fails**: Verify `BACKEND_URL` in frontend `.env`  
**Email not working**: Check OAuth tokens and credentials  
**WhatsApp fails**: Verify webhook URL and signature secret  
**No KB results**: Run `python scripts/seed_knowledge_base.py`

---

## 📖 Additional Resources

- [Terminal Output](docs/terminal-output.md)
- [Requirements Checklist](specs/001-multi-channel/checklists/requirements.md)
- [Quick Start Guide](specs/001-multi-channel/quickstart.md)
- [Research Notes](specs/001-multi-channel/research.md)

---

## 🤝 Contributing

1. Create feature branch from `main`
2. Follow code style (PEP 8, ESLint)
3. Add tests for new features
4. Update documentation
5. Run tests before PR

---

**Version**: 1.0.0 | **Updated**: 2026-05-14 | **License**: MIT
