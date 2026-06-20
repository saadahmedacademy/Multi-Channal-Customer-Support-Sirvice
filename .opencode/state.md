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
- `.opencode/context.md` — Updated conventions with security tooling info

## Next Steps
1. Run migration `004_add_message_feedback.sql` on Supabase
2. Push to deploy
3. Test multi-turn chat on web + WhatsApp + email

---

# Session State — 2026-06-17

## Current Task
Web form session isolation — each submission creates a fresh conversation + ticket

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
- `backend/api/routes/web_form.py` — Removed `get_active_by_customer` + `get_by_conversation_id`; always creates new conversation + ticket unconditionally
- `tests/api/test_web_form_endpoints.py` — Updated 4 tests to expect new behavior (always creates new session); removed stale mocks
- `.opencode/context.md` — Re-scanned project; updated repos (survey→message), routes, frontend API count, web_form convention

## Next Steps
1. Run migration `004_add_message_feedback.sql` on Supabase
2. Push to deploy
3. Test multi-turn chat on web + WhatsApp + email
