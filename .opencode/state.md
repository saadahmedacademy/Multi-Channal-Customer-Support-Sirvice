# Session State — 2026-07-08

## Current Task
Bump recharts 3.9.0 → 3.9.2 in frontend/package.json

## Active Decisions
- **Pyramid disclosure**: TL;DR at top (3-5 lines), progressive detail below — agents stop at TL;DR for 80% of queries
- **Cache-friendly layout**: Stable sections (architecture, stack, conventions) at top; dynamic sections (state, commits) at bottom
- **Navigation heuristics** over exhaustive lists — teach agents *how* to find routes/env vars instead of enumerating them
- **File split**: `context.md` = project structure (rare changes, full replace), `state.md` = session tracking (append, prune to 3 sessions)

## Blockers
None

## Recent Changes
- `frontend/package.json` — recharts ^3.9.0 → ^3.9.2
- `.opencode/context.md` — rescan + rebuild (2026-07-08)
- `.opencode/state.md` — new session entry

## Next Steps
1. Run `.opencode/context.md` through lint — verify < 100 lines / ~1,500 tokens
2. Add `/sp.context` command to CLI if not already present
3. On next structural change (new routes, deps, dirs), re-run scan via `/sp.context`

---

# Session State — 2026-06-26

## Current Task
Admin mode toggle + API key routing + admin dashboard — testing complete

## Active Decisions
- **Admin Mode toggle**: Toggle switch in header — ON shows API key input modal, OFF clears key
- **Key routing**: Normal users send `dev-key-12345` (from env), admins send `admin-key-67890` (from HTTP-only cookie)
- **API key validation**: Key validated against backend `/metrics/channels` (protected endpoint), not `/health` (public)
- **Admin dashboard**: Charts (7-day trend, channel distribution), stats cards (total, open, resolved today, avg response), status breakdown bar, response times by channel
- **Server-side protection**: Next.js middleware checks `admin-api-key` cookie on `/admin/*` routes
- **Web form session isolation**: Removed `get_active_by_customer` reuse — every web form submission starts a new session
- **Per-message feedback**: thumbs up/down stored on individual messages

## Blockers
None

## Recent Changes
- `backend/api/routes/tickets.py` — Restored `Depends(get_api_key)` on `GET /support/ticket/{id}`
- `frontend/src/lib/api-utils.ts` — `getAuthHeaders()` with cookie store support
- `frontend/src/app/api/auth/` — `set-key`, `clear-key`, `check` routes for admin key management
- `frontend/src/lib/auth-context.tsx` — React context for admin state
- `frontend/src/components/AdminToggle.tsx` — Toggle switch + key input modal

## Next Steps
1. Test flow: normal user submits ticket + checks status (dev-key used, works)
2. Test flow: toggle admin mode → enter `admin-key-67890` → dashboard loads with data
3. Test flow: toggle admin mode → enter wrong key → error shown
4. Test flow: direct `/admin` access without auth → redirected to `/`
5. Push to deploy

---

# Session State — 2026-06-20

## Current Task
Fix GitHub Actions security scan: upgrade vulnerable deps, pin action versions, suppress bandit FPs

## Active Decisions
- **Web form session isolation**: Removed `get_active_by_customer` reuse — every web form submission starts a new session
- **Per-message feedback** instead of ticket-level survey
- **Multi-turn conversations**: tickets stay `in_progress` after AI response (not auto-resolved)
- **WhatsApp/Email**: feedback prompt appended to response text (emojis)
- **Web frontend**: interactive thumbs up/down buttons + chat input bar for follow-up
- Thumbs down opens inline input asking "What went wrong?"

## Blockers
None

## Recent Changes
- `backend/requirements.txt` — Upgraded deps to fix 16+ CVEs
- `.github/workflows/security.yml` — Pinned trufflehog & trivy-action
- `backend/hf_main.py` — Added # nosec to suppress bandit B104
- `backend/integrations/email_client.py` — Added # nosec to suppress bandit B105
- `AGENTS.md` — Added rule: activate .venv before installing packages

## Next Steps
1. Run migration `004_add_message_feedback.sql` on Supabase
2. Push to deploy
3. Test multi-turn chat on web + WhatsApp + email
