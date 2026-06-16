"""Survey repository for ticket feedback."""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from backend.db.connection import db


class SurveyRepository:
    """Repository for ticket survey database operations."""

    async def save_survey(
        self,
        ticket_id: UUID,
        rating: str,
        reason: Optional[str] = None,
        source: str = "direct"
    ) -> Dict[str, Any]:
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO ticket_surveys (ticket_id, rating, reason, source)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (ticket_id)
                DO UPDATE SET rating = $2, reason = $3, source = $4, created_at = NOW()
                RETURNING id, ticket_id, rating, reason, source, created_at
            """, ticket_id, rating, reason, source)
            return dict(row)

    async def get_by_ticket_id(self, ticket_id: UUID) -> Optional[Dict[str, Any]]:
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, ticket_id, rating, reason, source, created_at
                FROM ticket_surveys
                WHERE ticket_id = $1
            """, ticket_id)
            return dict(row) if row else None


survey_repo = SurveyRepository()
