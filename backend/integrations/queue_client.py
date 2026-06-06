"""Redpanda/Kafka queue client with local in-process fallback for single-container deployments."""

import asyncio
import json
import os
from typing import Optional, Callable, Any, Dict
from datetime import datetime

TOPICS = {
    "tickets_incoming": "fte.tickets.incoming",
    "tickets_outgoing": "fte.tickets.outgoing",
    "escalations": "fte.escalations",
    "metrics": "fte.metrics",
    "dlq": "fte.dlq"
}

USE_LOCAL_QUEUE = os.getenv("QUEUE_MODE", "").lower() == "local"

if USE_LOCAL_QUEUE:

    class QueueClient:
        """In-process async queue implementation (no Kafka needed)."""

        def __init__(self):
            self._queues: Dict[str, asyncio.Queue] = {}
            self._consumer_task: Optional[asyncio.Task] = None
            self._running = False
            self._handler: Optional[Callable] = None

        async def start_producer(self) -> None:
            pass

        async def stop_producer(self) -> None:
            pass

        async def start_consumer(
            self,
            topics: list,
            group_id: str = "fte-message-processor"
        ) -> None:
            for topic in topics:
                self._queues.setdefault(topic, asyncio.Queue())
            self._running = True

        async def stop_consumer(self) -> None:
            self._running = False
            if self._consumer_task:
                self._consumer_task.cancel()
                try:
                    await self._consumer_task
                except (asyncio.CancelledError, Exception):
                    pass
                self._consumer_task = None

        async def publish(
            self,
            topic: str,
            message: Dict[str, Any],
            key: Optional[str] = None
        ) -> None:
            message["_publish_topic"] = topic
            message["timestamp"] = datetime.utcnow().isoformat()
            self._queues.setdefault(topic, asyncio.Queue())
            await self._queues[topic].put((topic, message))

        async def consume(
            self,
            handler: Callable[[str, Dict[str, Any]], Any],
            timeout_ms: int = 1000
        ) -> None:
            self._handler = handler
            self._running = True
            timeout = timeout_ms / 1000.0
            try:
                while self._running:
                    pending = []
                    for topic, q in list(self._queues.items()):
                        pending.append(asyncio.create_task(q.get(), name=topic))
                    if not pending:
                        await asyncio.sleep(timeout)
                        continue
                    done, pending_set = await asyncio.wait(
                        pending, timeout=timeout, return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in done:
                        try:
                            topic, message = task.result()
                            await handler(topic, message)
                        except Exception as e:
                            print(f"Error in local queue handler: {e}")
                    for task in pending_set:
                        task.cancel()
            except asyncio.CancelledError:
                pass

        @property
        def producer(self) -> bool:
            return True

else:
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

    class QueueClient:
        """Kafka/Redpanda queue client."""

        def __init__(self):
            self._producer: Optional[AIOKafkaProducer] = None
            self._consumer: Optional[AIOKafkaConsumer] = None
            self._bootstrap_servers = os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092"
            )

        async def start_producer(self) -> None:
            if self._producer is not None:
                return
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await self._producer.start()
            print(f"Kafka producer started, connecting to {self._bootstrap_servers}")

        async def stop_producer(self) -> None:
            if self._producer:
                await self._producer.stop()
                self._producer = None
                print("Kafka producer stopped")

        async def start_consumer(
            self,
            topics: list,
            group_id: str = "fte-message-processor"
        ) -> None:
            if self._consumer is not None:
                return
            self._consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self._bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            await self._consumer.start()
            print(f"Kafka consumer started for topics: {topics}")

        async def stop_consumer(self) -> None:
            if self._consumer:
                await self._consumer.stop()
                self._consumer = None
                print("Kafka consumer stopped")

        async def publish(
            self,
            topic: str,
            message: Dict[str, Any],
            key: Optional[str] = None
        ) -> None:
            if self._producer is None:
                await self.start_producer()
            message["timestamp"] = datetime.utcnow().isoformat()
            await self._producer.send_and_wait(topic, message, key=key)

        async def consume(
            self,
            handler: Callable[[str, Dict[str, Any]], Any],
            timeout_ms: int = 1000
        ) -> None:
            if self._consumer is None:
                raise RuntimeError("Consumer not started. Call start_consumer() first.")
            try:
                async for msg in self._consumer:
                    try:
                        await handler(msg.topic, msg.value)
                    except Exception as e:
                        print(f"Error processing message from {msg.topic}: {e}")
            except Exception as e:
                print(f"Consumer error: {e}")
                raise

        @property
        def producer(self) -> Optional[AIOKafkaProducer]:
            return self._producer

        @property
        def consumer(self) -> Optional[AIOKafkaConsumer]:
            return self._consumer


queue_client = QueueClient()
