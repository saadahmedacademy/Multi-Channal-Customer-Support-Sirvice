"""Redpanda/Kafka queue client for async message processing."""

from typing import Optional, Callable, Any, Dict
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import os
from datetime import datetime


# Topic definitions
TOPICS = {
    "tickets_incoming": "fte.tickets.incoming",
    "tickets_outgoing": "fte.tickets.outgoing",
    "escalations": "fte.escalations",
    "metrics": "fte.metrics",
    "dlq": "fte.dlq"  # Dead letter queue
}


class QueueClient:
    """Client for Redpanda/Kafka message queue."""
    
    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
    
    async def start_producer(self) -> None:
        """Start the Kafka producer."""
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
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            print("Kafka producer stopped")
    
    async def start_consumer(
        self,
        topics: list,
        group_id: str = "fte-message-processor"
    ) -> None:
        """
        Start the Kafka consumer.
        
        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
        """
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
        """Stop the Kafka consumer."""
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
        """
        Publish a message to a topic.

        Args:
            topic: Topic name
            message: Message payload (dict)
            key: Optional message key for partitioning
        """
        # Auto-start producer if not started
        if self._producer is None:
            await self.start_producer()

        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()

        await self._producer.send_and_wait(topic, message, key=key)
    
    async def consume(
        self,
        handler: Callable[[str, Dict[str, Any]], Any],
        timeout_ms: int = 1000
    ) -> None:
        """
        Consume messages from subscribed topics.
        
        Args:
            handler: Async function to handle messages (topic, message)
            timeout_ms: Poll timeout in milliseconds
        """
        if self._consumer is None:
            raise RuntimeError("Consumer not started. Call start_consumer() first.")
        
        try:
            async for msg in self._consumer:
                try:
                    await handler(msg.topic, msg.value)
                except Exception as e:
                    print(f"Error processing message from {msg.topic}: {e}")
                    # Could publish to DLQ here
        except Exception as e:
            print(f"Consumer error: {e}")
            raise
    
    @property
    def producer(self) -> Optional[AIOKafkaProducer]:
        """Get the producer instance."""
        return self._producer
    
    @property
    def consumer(self) -> Optional[AIOKafkaConsumer]:
        """Get the consumer instance."""
        return self._consumer


# Global queue client instance
queue_client = QueueClient()
