"""
Knowledge Base Repository Tests.

Tests for semantic search, keyword search, and category filtering.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Fixtures ==============

@pytest.fixture
def mock_db_conn():
    """Mock database connection."""
    with patch('backend.db.repositories.knowledge_repo.db') as mock_db:
        mock_conn = AsyncMock()
        mock_db.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_db.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_db, mock_conn


@pytest.fixture
def knowledge_repo():
    """Create knowledge base repository instance."""
    from backend.db.repositories.knowledge_repo import KnowledgeBaseRepository
    return KnowledgeBaseRepository()


# ============== Semantic Search Tests ==============

class TestKnowledgeBaseSemanticSearch:
    """Tests for semantic search functionality.

    Currently falls back to keyword search since embedding generation
    requires an external API. Tests verify the delegation works.
    """

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_similar_delegates_to_keyword_search(self, knowledge_repo):
        """Test semantic search delegates to keyword search."""
        expected_results = [{"title": "API Auth", "content": "Content", "category": "howto"}]
        with patch.object(knowledge_repo, 'search_by_keyword', new=AsyncMock(return_value=expected_results)) as mock_keyword:
            results = await knowledge_repo.search_similar("How do I login?", limit=5, threshold=0.7)
            assert results == expected_results
            mock_keyword.assert_called_once_with("How do I login?", 5)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_similar_empty_results(self, knowledge_repo):
        """Test semantic search with no matches."""
        with patch.object(knowledge_repo, 'search_by_keyword', new=AsyncMock(return_value=[])) as mock_keyword:
            results = await knowledge_repo.search_similar("random query", limit=5)
            assert len(results) == 0
            mock_keyword.assert_called_once_with("random query", 5)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_similar_respects_limit(self, knowledge_repo):
        """Test that limit parameter is passed through."""
        with patch.object(knowledge_repo, 'search_by_keyword', new=AsyncMock(return_value=[])) as mock_keyword:
            await knowledge_repo.search_similar("query", limit=10)
            mock_keyword.assert_called_once_with("query", 10)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_similar_multiple_results(self, knowledge_repo):
        """Test semantic search with multiple results."""
        mock_entries = [
            {"title": "Getting Started", "content": "Content 1", "category": "howto"},
            {"title": "API Basics", "content": "Content 2", "category": "feature"},
            {"title": "Authentication", "content": "Content 3", "category": "howto"},
        ]
        with patch.object(knowledge_repo, 'search_by_keyword', new=AsyncMock(return_value=mock_entries)) as mock_keyword:
            results = await knowledge_repo.search_similar("API guide")
            assert len(results) == 3
            mock_keyword.assert_called_once_with("API guide", 5)


# ============== Keyword Search Tests ==============

class TestKnowledgeBaseKeywordSearch:
    """Tests for keyword-based search functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_keyword_title_match(self, knowledge_repo, mock_db_conn):
        """Test keyword search matches in title."""
        mock_db, mock_conn = mock_db_conn
        
        mock_entry = {
            "id": uuid4(),
            "title": "API Rate Limits",
            "content": "Information about rate limits",
            "category": "feature"
        }
        mock_conn.fetch = AsyncMock(return_value=[mock_entry])

        results = await knowledge_repo.search_by_keyword("rate")

        assert len(results) == 1
        assert "API" in results[0]["title"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_keyword_content_match(self, knowledge_repo, mock_db_conn):
        """Test keyword search matches in content."""
        mock_db, mock_conn = mock_db_conn
        
        mock_entry = {
            "id": uuid4(),
            "title": "Error Handling",
            "content": "How to handle rate limit errors",
            "category": "troubleshooting"
        }
        mock_conn.fetch = AsyncMock(return_value=[mock_entry])

        results = await knowledge_repo.search_by_keyword("rate limit")

        assert len(results) == 1
        assert "Error Handling" in results[0]["title"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_keyword_category_match(self, knowledge_repo, mock_db_conn):
        """Test keyword search matches by category."""
        mock_db, mock_conn = mock_db_conn
        
        mock_entry = {
            "id": uuid4(),
            "title": "How to reset password",
            "content": "Password reset instructions",
            "category": "howto"
        }
        mock_conn.fetch = AsyncMock(return_value=[mock_entry])

        results = await knowledge_repo.search_by_keyword("howto")

        assert len(results) == 1
        assert results[0]["category"] == "howto"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_keyword_empty_results(self, knowledge_repo, mock_db_conn):
        """Test keyword search with no matches."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        results = await knowledge_repo.search_by_keyword("nonexistent")

        assert len(results) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_keyword_respects_limit(self, knowledge_repo, mock_db_conn):
        """Test keyword search respects limit parameter."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        await knowledge_repo.search_by_keyword("test", limit=3)

        query = mock_conn.fetch.call_args[0][0]
        assert "$3" in query  # Third param placeholder

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_keyword_uses_ilike(self, knowledge_repo, mock_db_conn):
        """Test keyword search uses case-insensitive matching."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        await knowledge_repo.search_by_keyword("API")

        # Verify ILIKE is used (case-insensitive)
        query = mock_conn.fetch.call_args[0][0]
        assert "ILIKE" in query


# ============== Category Search Tests ==============

class TestKnowledgeBaseCategorySearch:
    """Tests for category-based filtering."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_category(self, knowledge_repo, mock_db_conn):
        """Test filtering by category."""
        mock_db, mock_conn = mock_db_conn
        
        mock_entries = [
            {"id": uuid4(), "title": "Getting API Key", "content": "Content 1", "category": "howto"},
            {"id": uuid4(), "title": "Resetting Password", "content": "Content 2", "category": "howto"}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_entries)

        results = await knowledge_repo.search_by_category("howto")

        assert len(results) == 2
        assert all(r["category"] == "howto" for r in results)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_category_empty(self, knowledge_repo, mock_db_conn):
        """Test category search with no entries."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        results = await knowledge_repo.search_by_category("nonexistent")

        assert len(results) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_search_by_category_respects_limit(self, knowledge_repo, mock_db_conn):
        """Test category search respects limit."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        await knowledge_repo.search_by_category("faq", limit=5)

        query = mock_conn.fetch.call_args[0][0]
        assert "$2" in query  # Second param placeholder


# ============== Get All Tests ==============

class TestKnowledgeBaseGetAll:
    """Tests for retrieving all knowledge base entries."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_all_entries(self, knowledge_repo, mock_db_conn):
        """Test getting all entries."""
        mock_db, mock_conn = mock_db_conn
        
        mock_entries = [
            {"id": uuid4(), "title": "Entry 1", "content": "Content 1", "category": "faq"},
            {"id": uuid4(), "title": "Entry 2", "content": "Content 2", "category": "howto"}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_entries)

        results = await knowledge_repo.get_all()

        assert len(results) == 2
        assert all("title" in r and "content" in r for r in results)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_all_respects_limit(self, knowledge_repo, mock_db_conn):
        """Test get all respects limit parameter."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        await knowledge_repo.get_all(limit=20)

        query = mock_conn.fetch.call_args[0][0]
        assert "$1" in query  # First param placeholder

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_all_ordered_by_date(self, knowledge_repo, mock_db_conn):
        """Test get all orders by created_at."""
        mock_db, mock_conn = mock_db_conn
        mock_conn.fetch = AsyncMock(return_value=[])

        await knowledge_repo.get_all()

        query = mock_conn.fetch.call_args[0][0]
        assert "ORDER BY created_at DESC" in query


# ============== Integration Tests ==============

class TestKnowledgeBaseIntegration:
    """Integration tests for knowledge base in message processing."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_load_knowledge_context_in_processor(self):
        """Test that message processor loads knowledge context."""
        from backend.worker.message_processor import MessageProcessor
        
        processor = MessageProcessor()
        
        # Verify method exists
        assert hasattr(processor, '_load_knowledge_context')
        
        # Verify it's async
        import asyncio
        assert asyncio.iscoroutinefunction(processor._load_knowledge_context)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_knowledge_context_with_semantic_fallback(self):
        """Test knowledge loading falls back to keyword search."""
        from backend.worker.message_processor import MessageProcessor
        from backend.db.repositories.knowledge_repo import knowledge_repo
        
        processor = MessageProcessor()
        
        with patch.object(knowledge_repo, 'search_similar', return_value=[]) as mock_semantic:
            with patch.object(knowledge_repo, 'search_by_keyword', return_value=[
                {"title": "Test", "content": "Test content", "category": "faq"}
            ]) as mock_keyword:
                
                context = await processor._load_knowledge_context("How does API work?")
                
                # Should fallback to keyword search
                mock_semantic.assert_called_once()
                mock_keyword.assert_called_once()
                assert len(context) == 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_knowledge_context_with_stop_words(self):
        """Test that stop words are filtered from queries."""
        from backend.worker.message_processor import MessageProcessor
        from backend.db.repositories.knowledge_repo import knowledge_repo
        
        processor = MessageProcessor()
        
        with patch.object(knowledge_repo, 'search_similar', return_value=[]):
            with patch.object(knowledge_repo, 'search_by_keyword', return_value=[]) as mock_keyword:
                
                await processor._load_knowledge_context("What is the API?")
                
                # Should extract "API" as keyword (filtering "what", "is", "the")
                call_args = mock_keyword.call_args
                keyword = call_args[1]['keyword'] if 'keyword' in call_args[1] else call_args[0][0]
                # Keyword should be "api" (lowercase, without question mark)
                assert "api" in keyword.lower()


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
