"""Unified entry point for Hugging Face Spaces single-container deployment.

Sets QUEUE_MODE=local to use in-process async queue instead of Kafka,
then runs both the FastAPI backend and message processor worker
in the same process.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["QUEUE_MODE"] = "local"

import asyncio
import base64
import signal
import logging
import uvicorn

from backend.api.main import app
from backend.config.settings import settings
from backend.config.logging import get_logger
from backend.db.connection import init_db, close_db
from backend.integrations.queue_client import queue_client, TOPICS
from backend.integrations.email_client import gmail_client
from backend.worker.message_processor import MessageProcessor

logger = get_logger(__name__)
PORT = int(os.getenv("PORT", "7860"))
EMAIL_SYNC_INTERVAL = int(os.getenv("EMAIL_SYNC_INTERVAL", "30"))


async def run_worker(stop_event: asyncio.Event) -> None:
    processor = MessageProcessor()
    await queue_client.start_consumer(
        topics=[TOPICS["tickets_incoming"], TOPICS["escalations"]],
        group_id="fte-message-processor"
    )
    logger.info("HF local worker consumer started")
    worker_task = asyncio.create_task(
        queue_client.consume(processor.handle_message)
    )
    await stop_event.wait()
    await queue_client.stop_consumer()
    worker_task.cancel()
    try:
        await worker_task
    except (asyncio.CancelledError, Exception):
        pass
    logger.info("Worker stopped")


async def sync_gmail_emails(max_results: int = 10) -> int:
    """Fetch unread support emails from Gmail and queue for processing."""
    if not gmail_client.is_configured():
        return 0

    try:
        result = await gmail_client.list_messages(
            query=f"is:unread to:{gmail_client.support_email}",
            max_results=max_results
        )

        if "error" in result:
            logger.warning(f"Gmail sync error: {result['error']}")
            return 0

        messages = result.get("messages", [])
        if not messages:
            return 0

        processed = 0
        for msg_summary in messages:
            message_id = msg_summary.get("id")
            if not message_id:
                continue

            msg_data = await gmail_client.get_message(message_id, format="full")
            if "error" in msg_data:
                continue

            payload = msg_data.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

            subject = headers.get("Subject", "")
            from_header = headers.get("From", "")
            in_reply_to = headers.get("In-Reply-To", "")

            from_email = from_header
            if "<" in from_header and ">" in from_header:
                from_email = from_header.split("<")[1].split(">")[0].strip()

            body = ""
            html_body = ""

            def extract_body(part):
                nonlocal body, html_body
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                elif part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                    html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                elif "parts" in part:
                    for subpart in part["parts"]:
                        extract_body(subpart)

            extract_body(payload)

            email_payload = {
                "type": "email_message",
                "channel": "email",
                "from_email": from_email,
                "from_name": from_header.split("<")[0].strip() if "<" in from_header else "",
                "message_id": message_id,
                "content": body or html_body,
                "subject": subject,
                "is_reply": bool(in_reply_to),
                "in_reply_to": in_reply_to,
                "html_body": html_body,
            }

            await queue_client.publish(
                topic=TOPICS["tickets_incoming"],
                message=email_payload,
                key=from_email,
            )
            await gmail_client.mark_as_read(message_id)
            processed += 1
            logger.info(f"Auto-synced email {message_id} from {from_email}")

        logger.info(f"Gmail auto-sync: {processed} email(s) processed")
        return processed

    except Exception as e:
        logger.error(f"Gmail auto-sync error: {e}", exc_info=True)
        return 0


async def periodic_email_sync(stop_event: asyncio.Event) -> None:
    """Periodically check for new support emails."""
    while not stop_event.is_set():
        try:
            await sync_gmail_emails()
        except Exception as e:
            logger.error(f"Periodic email sync failed: {e}")
        try:
            await asyncio.wait_for(
                asyncio.get_event_loop().create_future(),
                timeout=EMAIL_SYNC_INTERVAL,
            )
        except asyncio.TimeoutError:
            pass
        except (asyncio.CancelledError, Exception):
            break


async def shutdown(
    server: uvicorn.Server,
    worker_stop: asyncio.Event,
) -> None:
    logger.info("Shutdown signal received, stopping services...")
    worker_stop.set()
    server.should_exit = True


async def main() -> None:
    await init_db(settings.database_url)
    logger.info("Database pool initialized")

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    worker_stop = asyncio.Event()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(
                sig, lambda: asyncio.create_task(shutdown(server, worker_stop))
            )
        except NotImplementedError:
            pass

    await asyncio.gather(
        run_worker(worker_stop),
        periodic_email_sync(worker_stop),
        server.serve(),
    )

    await close_db()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
