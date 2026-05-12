#!/usr/bin/env python3
"""
Create Kafka/Redpanda topics for AI Customer Support Agent.

This script creates all required topics for the message queue system.
Run this after starting Redpanda and before starting the worker.

Usage:
    python backend/scripts/create_topics.py
"""

import asyncio
import os
import sys
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config.logging import get_logger

logger = get_logger(__name__)

# Topic definitions
TOPICS = {
    "tickets_incoming": {
        "name": "fte.tickets.incoming",
        "description": "Incoming support requests from all channels",
        "num_partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": 604800000,  # 7 days
            "cleanup.policy": "delete"
        }
    },
    "tickets_outgoing": {
        "name": "fte.tickets.outgoing",
        "description": "Outgoing responses to customers",
        "num_partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": 604800000,  # 7 days
            "cleanup.policy": "delete"
        }
    },
    "escalations": {
        "name": "fte.escalations",
        "description": "Tickets escalated to human agents",
        "num_partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": 2592000000,  # 30 days
            "cleanup.policy": "delete"
        }
    },
    "metrics": {
        "name": "fte.metrics",
        "description": "System metrics and monitoring data",
        "num_partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": 86400000,  # 1 day
            "cleanup.policy": "delete"
        }
    },
    "dlq": {
        "name": "fte.dlq",
        "description": "Dead letter queue for failed messages",
        "num_partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": 604800000,  # 7 days
            "cleanup.policy": "delete"
        }
    }
}


async def create_topics(bootstrap_servers: str = "localhost:9092"):
    """
    Create all required Kafka topics.

    Args:
        bootstrap_servers: Kafka/Redpanda bootstrap servers
    """
    print(f"🔌 Connecting to Kafka/Redpanda at {bootstrap_servers}...")

    # Create admin client
    admin_client = AIOKafkaAdminClient(
        bootstrap_servers=bootstrap_servers,
        client_id="topic-creator"
    )

    try:
        await admin_client.start()
        print("✅ Connected to Kafka/Redpanda")

        # Create topics
        topics_to_create = []
        for topic_key, topic_config in TOPICS.items():
            topic = NewTopic(
                name=topic_config["name"],
                num_partitions=topic_config["num_partitions"],
                replication_factor=topic_config["replication_factor"],
                topic_configs=topic_config.get("config")
            )
            topics_to_create.append(topic)

        print(f"\n📦 Creating {len(topics_to_create)} topics...")
        print("=" * 60)

        # Create all topics
        results = await admin_client.create_topics(
            new_topics=topics_to_create,
            validate_only=False
        )

        # Process results
        for topic_key, topic_config in TOPICS.items():
            topic_name = topic_config["name"]
            future = results.get(topic_name)

            if future is None:
                print(f"✅ {topic_name}")
                print(f"   Partitions: {topic_config['num_partitions']}")
                print(f"   Retention: {topic_config['config']['retention.ms'] / 3600000:.0f} hours")
            else:
                try:
                    await future
                    print(f"✅ {topic_name}")
                except TopicAlreadyExistsError:
                    print(f"⚠️  {topic_name} (already exists)")
                except Exception as e:
                    print(f"❌ {topic_name} - Error: {e}")

        print("=" * 60)

        # List all topics
        print("\n📋 Listing all topics...")
        all_topics = await admin_client.list_topics()
        fte_topics = [t for t in all_topics if t.startswith("fte.")]

        if fte_topics:
            print("\n✅ FTE Topics created:")
            for topic in sorted(fte_topics):
                print(f"   - {topic}")
        else:
            print("\n⚠️  No FTE topics found")

        print("\n✨ Topic creation complete!")

    except Exception as e:
        print(f"\n❌ Error creating topics: {e}")
        logger.error(f"Failed to create topics: {e}", exc_info=True)
        sys.exit(1)

    finally:
        await admin_client.close()


async def main():
    """Main entry point."""
    # Get bootstrap servers from environment or use default
    bootstrap_servers = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )

    print("=" * 60)
    print("🚀 AI Customer Support Agent - Topic Creator")
    print("=" * 60)
    print()

    await create_topics(bootstrap_servers)

    print()
    print("Next steps:")
    print("  1. Start the backend: uvicorn backend.api.main:app --reload")
    print("  2. Start the worker: python backend/worker/message_processor.py")
    print("  3. Start the frontend: cd frontend && npm run dev")


if __name__ == "__main__":
    asyncio.run(main())
