---
description: Maintain a layered, token-efficient project context at .opencode/context.md and session state at .opencode/state.md. Uses pyramid disclosure — ultra-condensed TL;DR at top, details below. Separates static project structure from dynamic session state for minimal re-read cost.
handoffs:
  - label: Refresh State
    agent: sp.context
    prompt: Update current session state
    send: false
---

## Goal

Maintain **two files** that together give a new session full project awareness in 1-2 reads (~200 tokens for TL;DR, ~2K tokens for full):

| File | Content | Changes | Purpose |
|------|---------|---------|---------|
| `.opencode/context.md` | Architecture, stack, conventions, key files, deploy targets | Rare (project structure) | Bootstraps project awareness |
| `.opencode/state.md` | Current work, decisions, blockers, recent changes | Every session | Tracks what's in progress |

## Core Principles (from 2026 Context Engineering Research)

### Pyramid Disclosure
The file is structured as nested layers of detail. The top **must** be a TL;DR that fully identifies the project in 3-5 lines — agents can stop there for 80% of queries and only drill down when needed.

### Cache-Friendly Layout
Stable sections at the top (architecture, stack, conventions), dynamic sections at the bottom (commits, active work). This mimics Anthropic prompt caching — the stable prefix stays identical across reads, enabling provider-side KV cache reuse.

### Navigation Heuristics Over Exhaustive Lists
Instead of enumerating every API route and env var, teach the agent *how* to find them. A 2-line navigation pattern replaces a 30-line table. The agent explores just-in-time using tools, keeping context lean.

### Write State, Don't Carry It
Session state (current task, decisions, blockers) lives in `.opencode/state.md`, not in the agent's context window. The agent writes progress there and reads it back after context resets. This is Anthropic's "structured note-taking" pattern.

## Execution Steps

### Phase 1: Detect Changes (30s)

Run `git diff --name-only HEAD~1..HEAD` to list files changed since last commit.

- If **only** `.opencode/context.md` or `.opencode/state.md` changed — skip regeneration, just update state (jump to Phase 4).
- If project structure files changed (routes, deps, config, new dirs) — proceed to Phase 2.
- If no context files exist yet or `git` fails — proceed to Phase 2 (full scan).

### Phase 2: Scan (Single Parallel Batch)

Read all of these in **one** parallel call:

**Root markers (3 files):**
- `README.md` — project name, description, badges
- `pyproject.toml` — test config, lint config, Python deps
- `package.json` (root, if exists) — workspace scripts

**Backend skeleton:**
- `backend/api/main.py` — registered route prefixes + middleware list (just first 20 lines + router includes)
- `ls backend/api/routes/` — file names only
- `ls backend/db/repositories/` — file names only
- `ls backend/integrations/` — file names only
- `ls backend/worker/` — file names only
- `ls backend/api/middleware/` — file names only
- `backend/config/settings.py` — extract `Field(...)` lines via `rg Field\(` or grep

**Frontend skeleton:**
- `ls frontend/src/app/` — subdirectory names only
- `frontend/package.json` — name, scripts, key deps (tailwind, next, react)

**Infra skeleton:**
- `ls .github/workflows/` — file names only
- `Dockerfile` — first 5 lines (base image + entry point)
- `docker-compose.yml` — service names only (first 10 lines)

**State (if exists):**
- `.opencode/state.md` — read existing state

### Phase 3: Build/Update `.opencode/context.md`

Generate the file using this **pyramid structure**. Start with the TL;DR, then add progressive detail.

```markdown
# <project-name>

> <one-line description> · Backend: <tech> · Frontend: <tech> · DB: <db> · AI: <provider chain>

Scanned: <YYYY-MM-DD>

## Architecture
<2-3 line system diagram in prose>

## Stack
| Layer | Tech |
|-------|------|
| Backend | Python X.Y + FastAPI |
| Frontend | Next.js X + React X + Tailwind CSS X |
| Database | PostgreSQL (asyncpg pool X-Y) |
| Queue | Redpanda / local in-process fallback |
| AI | <fallback chain> |
| Email | Gmail API (OAuth2) |
| WhatsApp | Meta Cloud API |

## Key Files
| Path | Role |
|------|------|
| backend/api/main.py | FastAPI app + lifespan + middleware |
| backend/api/routes/ | 9 route modules — <list names> |
| backend/config/settings.py | Pydantic settings (X env vars) |
| backend/db/connection.py | asyncpg pool manager |
| backend/db/repositories/ | X repos — <list names> |
| backend/integrations/ | <list names> |
| backend/worker/ | <list names> |
| backend/hf_main.py | HF Spaces unified entry (app + worker + email sync) |
| frontend/src/app/ | Next.js App Router (X pages, X API routes) |
| .github/workflows/ | <list names> |

## Navigation Patterns
- **API routes**: Read `backend/api/routes/<name>.py` — each file contains its own route group with `@router.get/post/...` annotations.
- **Env vars**: Search for `Field(...)` in `backend/config/settings.py` — each field is one env var with default and type.
- **DB schema**: See `database/schema.sql` for full DDL, or `backend/db/repositories/` for query patterns.
- **Frontend pages**: Each dir under `frontend/src/app/` is a route; `page.tsx` = page, `route.ts` = API, `layout.tsx` = layout.
- **Conventions**: Linter=<lint>, Formatter=<fmt>, Test=<test-cmd>, CSS=<css-framework>, Commit=<commit-style>.

## Conventions
- <lint> · <fmt> · <test runner> · <CSS> · <commit style>
- <notable patterns: raw SQL vs ORM, sanitization, error handling style>

## Deploy Targets
| Target | URL |
|--------|-----|
| HF Spaces | <url> |
| Vercel | <url> |
```

### Phase 4: Update `.opencode/state.md`

Merge existing state (if any) with new session state. The file structure:

```markdown
# Session State — <YYYY-MM-DD>

## Current Task
<what is being worked on right now — 1 line>

## Active Decisions
- <decision 1>
- <decision 2>

## Blockers
- <blocker 1> — <why blocked>

## Recent Changes
- <last 5 changed files with brief description>

## Next Steps
1. <step 1>
2. <step 2>
```

**Merge behavior:**
- If `Current Task` is empty from prior session, wipe it.
- If `Active Decisions` exist from prior session, keep them and append new ones.
- If `Blockers` are resolved, remove them.
- If `Recent Changes` exceed 5, keep only the 5 most recent.
- If `Next Steps` exist, keep them and add new ones below (don't overwrite).

### Phase 5: Prune

- `.opencode/context.md`: Keep only the **current** snapshot (replace, don't append). Project structure rarely changes — no need for history.
- `.opencode/state.md`: Keep the 3 most recent session entries. Prune older ones.

### Phase 6: Report

```
Context:  .opencode/context.md (XX lines, scanned YY files)
State:   .opencode/state.md (XX lines, ZZ active items)
```

## How to Load Context in a Session

When a session starts and `.opencode/context.md` exists:

1. **Read the first 5 lines** (title + TL;DR + architecture) — this covers 80% of queries.
2. If you need specifics (routes, env vars, file paths), **read the relevant section** using the navigation patterns in the file — don't load the whole thing unless necessary.
3. **Read `.opencode/state.md`** to understand what's in progress.
4. **Don't re-scan the repo** unless context.md is clearly stale (missing a known file) or the task requires probing deeper than what context.md describes.
5. If the project has changed structurally since the last scan, **run `/sp.context`** to regenerate.

## Token Budget

| Layer | Lines | Tokens (est.) | What |
|-------|-------|---------------|------|
| 1 — TL;DR | 3-5 | ~60 | Project name + one-liner + architecture |
| 2 — Key refs | 20-40 | ~500 | Stack table, key files, navigation patterns |
| 3 — Details | 30-60 | ~800 | Conventions, deploy targets |

**Total target**: Under 100 lines / ~1,500 tokens for context.md. Under 40 lines / ~600 tokens for state.md.

## Anti-Patterns (Don't)

- ❌ **Dumping full route tables** — navigation patterns are more token-efficient and stay valid as routes change.
- ❌ **Regenerating from scratch each time** — use `git diff` to detect real changes; skip if nothing changed.
- ❌ **Appending full snapshots** — replace context.md (static structure), append to state.md (dynamic).
- ❌ **Including tool outputs or raw config values** — pointers and summaries only.
- ❌ **Letting state.md grow unbounded** — prune to 3 sessions max.
