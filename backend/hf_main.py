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
import signal
import logging
import uvicorn

from backend.api.main import app
from backend.config.settings import settings
from backend.config.logging import get_logger
from backend.db.connection import init_db, close_db
from backend.integrations.queue_client import queue_client, TOPICS
from backend.worker.message_processor import MessageProcessor

logger = get_logger(__name__)
PORT = int(os.getenv("PORT", "7860"))


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
        server.serve(),
    )

    await close_db()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
