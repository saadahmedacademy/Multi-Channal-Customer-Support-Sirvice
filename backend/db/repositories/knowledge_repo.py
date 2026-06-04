"""Knowledge base repository for semantic search operations."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from backend.db.connection import db


class KnowledgeBaseRepository:
    """Repository for knowledge base semantic search operations."""

    async def search_similar(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for knowledge base entries similar to query.

        Falls back to keyword-based text search since embedding generation
        requires an external API (e.g., OpenAI, Gemini) that must be
        configured separately.

        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of knowledge base entries with similarity scores
        """
        return await self.search_by_keyword(query, limit)

    async def search_by_keyword(
        self,
        keyword: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base by keyword matching.

        Fallback when embeddings are not available.

        Args:
            keyword: Search keyword
            limit: Maximum number of results

        Returns:
            List of matching knowledge base entries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, title, content, category
                FROM knowledge_base
                WHERE title ILIKE $1
                   OR content ILIKE $1
                   OR category = $2
                ORDER BY
                    CASE
                        WHEN title ILIKE $1 THEN 1
                        ELSE 2
                    END,
                    created_at DESC
                LIMIT $3
            """, f"%{keyword}%", keyword, limit)

            return [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "category": row["category"]
                }
                for row in rows
            ]

    async def search_by_category(
        self,
        category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get knowledge base entries by category.

        Args:
            category: Category filter
            limit: Maximum number of results

        Returns:
            List of knowledge base entries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, title, content, category
                FROM knowledge_base
                WHERE category = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, category, limit)

            return [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "category": row["category"]
                }
                for row in rows
            ]

    async def get_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all knowledge base entries.

        Args:
            limit: Maximum number of results

        Returns:
            List of all knowledge base entries
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, title, content, category
                FROM knowledge_base
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)

            return [
                {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "content": row["content"],
                    "category": row["category"]
                }
                for row in rows
            ]


# Global repository instance
knowledge_repo = KnowledgeBaseRepository()
