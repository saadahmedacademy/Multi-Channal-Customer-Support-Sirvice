# Session State — 2026-06-16

## Current Task
Replaced old survey system with inline per-message feedback + multi-turn chat

## Active Decisions
- **Per-message feedback** instead of ticket-level survey: thumbs up/down stored on individual messages, not a separate table
- **Multi-turn conversations**: tickets stay `in_progress` after AI response (not auto-resolved); follow-up messages trigger AI with full history
- **WhatsApp/Email**: feedback prompt appended to response text (emojis), detected on reply → saved to latest agent message
- **Web frontend**: interactive thumbs up/down buttons + chat input bar for follow-up
- Thumbs down opens inline input asking "What went wrong?"

## Blockers
None

## Recent Changes
- `database/schema.sql` — Removed `ticket_surveys` table
- `database/migrations/004_add_message_feedback.sql` — New migration: add feedback columns to messages
- `backend/db/repositories/message_repo.py` — New repo: get_by_conversation, set_feedback, get_latest_agent_message
- `backend/api/schemas/messages.py` — Added FeedbackRating, FeedbackSubmit, FollowUpMessage, FollowUpResponse; added feedback fields to MessageSchema
- `backend/api/schemas/tickets.py` — Removed old SurveyRating, SurveySubmitRequest, SurveyResponse
- `backend/api/routes/tickets.py` — Removed POST /ticket/{ticket_id}/survey; uses message_repo
- `backend/api/routes/conversations.py` — Added POST /{id}/messages (follow-up) + POST /messages/{id}/feedback
- `backend/worker/message_processor.py` — No auto-resolve; feedback saves to last agent message; multi-turn support
- `frontend/src/components/TicketStatus.tsx` — Full rewrite: chat bubbles with 👍/👎 buttons, input bar, thumbs-down reason input
- `frontend/src/app/api/conversations/[id]/messages/route.ts` — New frontend API proxy
- `frontend/src/app/api/messages/[messageId]/feedback/route.ts` — New frontend API proxy

## Next Steps
1. Run migration `004_add_message_feedback.sql` on Supabase
2. Push to deploy
3. Test multi-turn chat on web + WhatsApp + email
