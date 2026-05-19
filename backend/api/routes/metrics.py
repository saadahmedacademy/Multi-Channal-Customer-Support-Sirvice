"""Channel metrics and analytics endpoint."""

from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from backend.db.connection import db
from backend.integrations.whatsapp_client import whatsapp_client
from backend.integrations.email_client import gmail_client
from backend.utils.auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metrics"])


@router.get("/channels", dependencies=[Depends(get_api_key)])
async def get_channel_metrics() -> Dict[str, Any]:
    """
    Get metrics for all support channels.

    **Authentication**: Requires X-API-Key header

    Returns statistics on tickets, messages, and response times per channel.
    """
    async with db.acquire() as conn:
        # Get ticket counts by channel and status
        ticket_rows = await conn.fetch("""
            SELECT 
                source_channel,
                status,
                COUNT(*) as count
            FROM tickets
            GROUP BY source_channel, status
        """)

        # Get message counts by channel
        message_rows = await conn.fetch("""
            SELECT 
                channel,
                direction,
                COUNT(*) as count
            FROM messages
            GROUP BY channel, direction
        """)

        # Get average response time (time between customer and agent messages)
        response_time_rows = await conn.fetch("""
            SELECT 
                m1.channel,
                AVG(EXTRACT(EPOCH FROM (m2.created_at - m1.created_at))) as avg_response_seconds
            FROM messages m1
            JOIN messages m2 ON m1.conversation_id = m2.conversation_id
                AND m1.direction = 'inbound'
                AND m2.direction = 'outbound'
                AND m2.created_at > m1.created_at
            GROUP BY m1.channel
        """)

        # Get today's stats
        today = datetime.utcnow().date()
        today_rows = await conn.fetch("""
            SELECT 
                source_channel,
                COUNT(*) as count
            FROM tickets
            WHERE DATE(created_at) = $1
            GROUP BY source_channel
        """, today)

    # Build ticket metrics by channel
    ticket_metrics = {}
    for row in ticket_rows:
        channel = row["source_channel"]
        if channel not in ticket_metrics:
            ticket_metrics[channel] = {"total": 0, "by_status": {}}
        ticket_metrics[channel]["by_status"][row["status"]] = row["count"]
        ticket_metrics[channel]["total"] += row["count"]

    # Build message metrics by channel
    message_metrics = {}
    for row in message_rows:
        channel = row["channel"]
        if channel not in message_metrics:
            message_metrics[channel] = {"inbound": 0, "outbound": 0}
        message_metrics[channel][row["direction"]] = row["count"]

    # Build response time metrics
    response_time_metrics = {}
    for row in response_time_rows:
        response_time_metrics[row["channel"]] = {
            "avg_seconds": round(row["avg_response_seconds"] or 0, 2),
            "avg_minutes": round((row["avg_response_seconds"] or 0) / 60, 2)
        }

    # Build today's stats
    today_metrics = {}
    for row in today_rows:
        today_metrics[row["source_channel"]] = row["count"]

    # Get WhatsApp rate limit status
    whatsapp_rate_limit = whatsapp_client.get_rate_limit_status()

    # Get Email rate limit status
    email_rate_limit = gmail_client.get_rate_limit_status()

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "tickets": {
            "by_channel": ticket_metrics,
            "today": today_metrics
        },
        "messages": {
            "by_channel": message_metrics
        },
        "response_times": response_time_metrics,
        "channels": {
            "whatsapp": {
                "rate_limit": whatsapp_rate_limit
            },
            "email": {
                "rate_limit": email_rate_limit
            }
        }
    }


@router.get("/tickets/summary")
async def get_ticket_summary(
    days: int = 7
) -> Dict[str, Any]:
    """
    Get ticket summary for the last N days.

    Args:
        days: Number of days to include
    """
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                DATE(created_at) as date,
                source_channel,
                status,
                COUNT(*) as count
            FROM tickets
            WHERE created_at >= NOW() - ($1 * INTERVAL '1 day')
            GROUP BY DATE(created_at), source_channel, status
            ORDER BY date DESC
        """, days)

    # Group by date
    by_date = {}
    for row in rows:
        date_str = str(row["date"])
        if date_str not in by_date:
            by_date[date_str] = {"total": 0, "by_channel": {}, "by_status": {}}
        
        by_date[date_str]["total"] += row["count"]
        by_date[date_str]["by_channel"][row["source_channel"]] = row["count"]
        by_date[date_str]["by_status"][row["status"]] = row["count"]

    return {
        "period_days": days,
        "by_date": by_date
    }
