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

## Test Results
| Test | Result |
|------|--------|
| Ticket endpoint without key → 401 | ✅ |
| Ticket endpoint with valid dev-key → 404 (key accepted) | ✅ |
| Ticket endpoint with valid admin-key → 404 (key accepted) | ✅ |
| Ticket endpoint with invalid key → 403 | ✅ |
| Health endpoint (public) → 200 | ✅ |
| Metrics endpoint without key → 401 | ✅ |
| Metrics endpoint with admin-key → 200 | ✅ |
| Auth check (no cookie) → `{keyPresent:false, isAdmin:false}` | ✅ |
| Set-key with valid admin-key → `{valid:true, isAdmin:true}` | ✅ |
| Set-key with invalid key → HTTP 401 | ✅ |
| Set-key with dev-key (valid, not admin) → `{valid:true, isAdmin:false}` | ✅ |
| Clear-key → cookie cleared | ✅ |
| Admin dashboard proxy (metrics) → HTTP 200 | ✅ |
| Admin page with admin cookie → HTTP 200 | ✅ |
| Admin page without cookie → HTTP 307 redirect | ✅ |

## Recent Changes
- `backend/api/routes/tickets.py` — Restored `Depends(get_api_key)` on `GET /support/ticket/{id}` (auth required, key sent by frontend proxy)
- `frontend/.env.local` — Added `INTERNAL_API_KEY=dev-key-12345` and `ADMIN_API_KEY=admin-key-67890`
- `frontend/src/lib/api-utils.ts` — `getAuthHeaders()` now accepts optional cookie store; reads `admin-api-key` cookie first, falls back to env var
- `frontend/src/app/api/auth/` — Created `set-key`, `clear-key`, `check` routes for admin key management
- `frontend/src/lib/auth-context.tsx` — React context for admin state (`isAdmin`, `enableAdmin`, `disableAdmin`)
- `frontend/src/components/AdminToggle.tsx` — Toggle switch + glassmorphism API key input modal
- `frontend/src/app/page.tsx` — Added AdminToggle to header
- `frontend/src/app/layout.tsx` — Wrapped with AuthProvider
- `frontend/src/middleware.ts` — Server-side protection for `/admin/*` (redirects to `/` if no admin cookie)
- `frontend/src/app/admin/page.tsx` — Admin dashboard with recharts (StatsCards, TicketTrendChart, ChannelDistribution, status bars, response times)
- `frontend/src/app/api/admin/` — Proxy routes for `/metrics/channels` and `/metrics/tickets/summary`
- `frontend/src/components/admin/` — StatsCards, TicketTrendChart, ChannelDistribution components
- All 5 frontend API proxy routes updated to pass `request.cookies` to `getAuthHeaders()`

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
- **Web form session isolation**: Removed `get_active_by_customer` reuse — every web form submission starts a new session. Follow-ups via chat bar stay within that session.
- **Per-message feedback** instead of ticket-level survey: thumbs up/down stored on individual messages, not a separate table
- **Multi-turn conversations**: tickets stay `in_progress` after AI response (not auto-resolved); follow-up messages trigger AI with full history
- **WhatsApp/Email**: feedback prompt appended to response text (emojis), detected on reply → saved to latest agent message
- **Web frontend**: interactive thumbs up/down buttons + chat input bar for follow-up
- Thumbs down opens inline input asking "What went wrong?"

## Blockers
None

## Recent Changes
- `backend/requirements.txt` — Upgraded aiohttp≥3.14.0, fastapi≥0.135.0, python-multipart≥0.0.31, bleach≥6.4.0, pydantic≥2.5.3 to fix 16+ CVEs
- `.github/workflows/security.yml` — Pinned trufflehog@v3.82.12 & trivy-action@0.29.0; dropped bandit[toml] extra
- `backend/hf_main.py` — Added # nosec to suppress bandit B104 (expected 0.0.0.0 bind)
- `backend/integrations/email_client.py` — Added # nosec to suppress bandit B105 (Google OAuth URL)
- `AGENTS.md` — Added rule: activate .venv before installing packages

## Next Steps
1. Run migration `004_add_message_feedback.sql` on Supabase
2. Push to deploy
3. Test multi-turn chat on web + WhatsApp + email
