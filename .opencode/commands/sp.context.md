---
description: Scan project structure and maintain a token-efficient context file at .opencode/context.md. Run once per session to restore full project awareness without re-reading the entire codebase.
---

## Goal

Generate and maintain `.opencode/context.md` — a compact (~150 lines), high-signal project snapshot that lets future sessions bootstrap full context in seconds instead of re-scanning the entire repo.

The file is append-only: each run prepends a timestamped snapshot and keeps the previous one (max 3). Old entries are pruned.

## Execution Steps

### 1. Initialize

Determine project root (`.` from command invocation). Verify these exist:
- `backend/api/main.py` — FastAPI entry point
- `frontend/src/app/layout.tsx` — Next.js root layout
- `docker-compose.yml` or `Dockerfile` — container config

### 2. Scan Project Structure (Read Commands — 1 batch)

Run these reads in a **single parallel batch** (minimize round trips):

**Backend:**
- `backend/api/main.py` — registered routes, routers, middleware
- `backend/api/routes/` — list directory, note each file
- `backend/config/settings.py` — env vars, defaults, secrets
- `backend/db/connection.py` — DB type, pool config
- `backend/db/repositories/` — list directory
- `backend/integrations/` — list directory (email_client, queue_client, whatsapp_client)
- `backend/worker/` — list directory (message_processor, ai_agent)
- `backend/hf_main.py` — HF Spaces entry point (if exists)
- `pyproject.toml` — test config, lint config, deps

**Frontend:**
- `frontend/src/app/` — list directory (pages, API routes)
- `frontend/package.json` — scripts, key dependencies
- `frontend/next.config.ts` — build config

**Infra:**
- `Dockerfile` — container build steps
- `.github/workflows/` — list CI/CD files
- `docker-compose.yml` — service topology

### 3. Extract Env Vars (from settings.py)

Scan `settings.py` for `Field(...)` lines and note:
- Variable names + defaults
- Secrets (mark `SECRET`, `API_KEY`, `PASSWORD`, `TOKEN` — mask values)
- Required vs optional

### 4. Discover API Routes

Scan each file in `backend/api/routes/` for:
- `@router.*.get/post/put/patch/delete` — method + path
- `router.include_router` in `main.py`

Produce a compact route table.

### 5. Discover Frontend Pages

Scan each file/dir in `frontend/src/app/`:
- `page.tsx` = page route
- `route.ts` = API route
- `layout.tsx` = layout wrapper

### 6. Detect Conventions

From `pyproject.toml`:
- Linter (ruff/flake8/black)
- Formatter
- Test framework + runner

From `frontend/package.json`:
- Build tool + test tool
- CSS framework (Tailwind, CSS modules)

From commit history (last 5 commits — `git log --oneline -5`):
- Commit style, branch naming

### 7. Build Context File

Generate `.opencode/context.md` with this structure (keep under 200 lines total):

```markdown
# Project Context — <project-name>

Scanned: <datetime>

## Architecture
<2-3 line summary of how backend + frontend + worker connect>

## Stack
| Layer | Tech | Version/Notes |
|-------|------|--------------|
| Backend | Python + FastAPI | ... |
| Frontend | Next.js + Tailwind | ... |
| Database | PostgreSQL | ... |
| Queue | Redpanda / local | ... |
| AI | OpenRouter → HF → Gemini | ... |
| Email | Gmail API (OAuth) | ... |

## Key Files
| Path | Purpose |
|------|---------|
| backend/api/main.py | FastAPI app, lifespan, middleware |
| ... | ... |

## API Routes
| Method | Path | Description |
|--------|------|-------------|
| POST | /support/submit | Web form submission |
| GET | /support/ticket/{id} | Ticket status |
| ... | ... | ... |

## Frontend Pages
| Route | Type | Description |
|-------|------|-------------|
| / | page | Support form |
| /ticket/[id] | page | Ticket status lookup |
| ... | ... | ... |

## Environment Variables
| Var | Default | Secret? | Required? |
|-----|---------|---------|-----------|
| DATABASE_URL | postgresql://... | yes | yes |
| ... | ... | ... | ... |

## Conventions
- Linter: ruff
- Formatter: black
- Test: pytest (async)
- Commit style: conventional-commits
- Branch: feature/ → main

## Deploy Targets
| Target | URL |
|--------|-----|
| HF Spaces | https://saadi786-ai-customer-support.hf.space |
| Vercel | https://multi-channal-customer-support-sirv.vercel.app |
```

### 8. Prune Old Snapshots

If file already exists with 3+ timestamps, keep only the 2 most recent + the new one. Remove older blocks.

### 9. Report Summary

Print:
```
Context updated → .opencode/context.md (XX lines, scanned YY files)
```

## Loading Context in Future Sessions

If `.opencode/context.md` exists at session start, the agent should:
1. Read it first (1 read → full project awareness)
2. Only re-scan files when context is stale or user asks about something not covered
3. Run this command again if project structure has changed significantly

## Operating Principles

- **Token efficiency**: Each line must pull its weight. No verbose dumps.
- **Append-only**: Never mutate past snapshots — only add new ones and prune oldest.
- **Discover, don't guess**: Extract from actual files, never hallucinate structure.
- **Speed**: Complete in 3-4 tool round trips (1 batch read, 1 write, optional git command).
- **No persistence side effects**: Only writes `.opencode/context.md`. Never modifies source code, config, or database.
