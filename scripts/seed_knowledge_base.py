"""
Seed knowledge base with initial data.

This script populates the knowledge_base table with product documentation
to provide context for AI responses.

Usage:
    python scripts/seed_knowledge_base.py

Requirements:
    - DATABASE_URL environment variable must be set
    - Optional: OPENAI_API_KEY for generating embeddings
"""

import asyncio
import asyncpg
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for text using OpenAI API.

    Args:
        text: Text to embed

    Returns:
        Embedding vector (1536 dimensions) or None if API not available
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not set, skipping embeddings")
        return None

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "text-embedding-ada-002",
                    "input": text
                },
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            embedding = data["data"][0]["embedding"]

            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


async def seed_knowledge_base(
    conn: asyncpg.Connection,
    kb_file: str = "context/knowledge_base.json",
    generate_embeddings: bool = True
) -> int:
    """
    Seed knowledge base from JSON file.

    Args:
        conn: Database connection
        kb_file: Path to knowledge base JSON file
        generate_embeddings: Whether to generate embeddings

    Returns:
        Number of entries inserted
    """
    # Read knowledge base file
    kb_path = Path(__file__).parent.parent / kb_file

    if not kb_path.exists():
        logger.error(f"Knowledge base file not found: {kb_path}")
        return 0

    with open(kb_path, 'r') as f:
        kb_entries = json.load(f)

    logger.info(f"Loaded {len(kb_entries)} knowledge base entries")

    # Clear existing entries (optional - comment out to preserve existing data)
    await conn.execute("DELETE FROM knowledge_base")
    logger.info("Cleared existing knowledge base entries")

    # Insert entries
    inserted = 0

    for entry in kb_entries:
        title = entry.get("title", "")
        content = entry.get("content", "")
        category = entry.get("category", "faq")

        # Validate category
        valid_categories = ["feature", "howto", "faq", "troubleshooting"]
        if category not in valid_categories:
            logger.warning(f"Invalid category '{category}' for entry '{title}', defaulting to 'faq'")
            category = "faq"

        # Generate embedding if enabled
        embedding = None
        if generate_embeddings:
            # Combine title and content for embedding
            text_to_embed = f"{title}\n\n{content}"
            embedding = await generate_embedding(text_to_embed)

        try:
            # Insert into database
            await conn.execute("""
                INSERT INTO knowledge_base (title, content, category, embedding)
                VALUES ($1, $2, $3, $4)
            """, title, content, category, embedding)

            inserted += 1
            logger.info(f"Inserted: {title} (category: {category})")

        except Exception as e:
            logger.error(f"Failed to insert '{title}': {e}")

    return inserted


async def main():
    """Main entry point."""
    logger.info("Starting knowledge base seeding...")

    # Check database URL
    if not settings.database_url:
        logger.error("DATABASE_URL not set in environment")
        sys.exit(1)

    # Check if embeddings should be generated
    generate_embeddings = bool(os.getenv("OPENAI_API_KEY"))

    if not generate_embeddings:
        logger.warning(
            "OPENAI_API_KEY not set. Knowledge base will be seeded without embeddings. "
            "Semantic search will not work until embeddings are generated."
        )

    # Connect to database
    try:
        # Disable statement cache for pgbouncer compatibility
        conn = await asyncpg.connect(settings.database_url, statement_cache_size=0)
        logger.info("Connected to database")

        # Seed knowledge base
        inserted = await seed_knowledge_base(
            conn,
            generate_embeddings=generate_embeddings
        )

        logger.info(f"Successfully seeded {inserted} knowledge base entries")

        # Verify insertion
        count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
        logger.info(f"Total knowledge base entries in database: {count}")

        await conn.close()

    except Exception as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)

    logger.info("Knowledge base seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
