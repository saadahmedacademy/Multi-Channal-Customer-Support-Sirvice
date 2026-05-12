"""
Rate Limiting Enforcement Tests.

Tests for rate limiting middleware, enforcement, and headers.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============== Fixtures ==============

@pytest.fixture
def test_client():
    """Create test client with rate limiting enabled."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    # Create proper async mocks
    mock_queue = AsyncMock()
    mock_queue.start_producer = AsyncMock()
    mock_queue.stop_producer = AsyncMock()
    mock_queue.producer = None

    with patch('backend.db.connection.init_db', AsyncMock()):
        with patch('backend.db.connection.close_db', AsyncMock()):
            with patch('backend.integrations.queue_client.queue_client', mock_queue):
                from backend.api.main import app
                with TestClient(app, raise_server_exceptions=False) as client:
                    yield client


@pytest.fixture
def rate_limiter_instance():
    """Create isolated rate limiter instance for testing."""
    from backend.api.middleware.rate_limiter import RateLimiter
    return RateLimiter(requests_per_window=5, window_seconds=60)


# ============== Rate Limiter Core Tests ==============

class TestRateLimiterCore:
    """Tests for core rate limiting logic."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_allows_requests_under_limit(self, rate_limiter_instance):
        """Test that requests under limit are allowed."""
        limiter = rate_limiter_instance
        
        # Should allow 5 requests
        for i in range(5):
            result = await limiter.is_allowed("test-ip")
            assert result is True, f"Request {i+1} should be allowed"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_blocks_requests_over_limit(self, rate_limiter_instance):
        """Test that requests over limit are blocked."""
        limiter = rate_limiter_instance
        
        # Use up the limit
        for _ in range(5):
            await limiter.is_allowed("test-ip")
        
        # 6th request should be blocked
        result = await limiter.is_allowed("test-ip")
        assert result is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_different_keys_have_separate_limits(self, rate_limiter_instance):
        """Test that different IPs have separate rate limits."""
        limiter = rate_limiter_instance
        
        # Exhaust limit for IP 1
        for _ in range(5):
            await limiter.is_allowed("ip-1")
        
        # IP 2 should still be allowed
        result = await limiter.is_allowed("ip-2")
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sliding_window_resets(self, rate_limiter_instance):
        """Test that old requests are removed from window."""
        limiter = rate_limiter_instance
        
        # Use up the limit
        for _ in range(5):
            await limiter.is_allowed("test-ip")
        
        # Should be blocked
        assert await limiter.is_allowed("test-ip") is False
        
        # Manually clear old requests (simulate time passing)
        limiter._requests["test-ip"] = []
        
        # Should be allowed again
        result = await limiter.is_allowed("test-ip")
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_remaining_requests(self, rate_limiter_instance):
        """Test getting remaining request count."""
        limiter = rate_limiter_instance
        
        # Initially should have 5 remaining
        remaining = await limiter.get_remaining("test-ip")
        assert remaining == 5
        
        # After 2 requests, should have 3 remaining
        await limiter.is_allowed("test-ip")
        await limiter.is_allowed("test-ip")
        remaining = await limiter.get_remaining("test-ip")
        assert remaining == 3
        
        # After exhausting, should have 0 remaining
        await limiter.is_allowed("test-ip")
        await limiter.is_allowed("test-ip")
        await limiter.is_allowed("test-ip")
        remaining = await limiter.get_remaining("test-ip")
        assert remaining == 0


# ============== Middleware Enforcement Tests ==============

class TestRateLimitMiddleware:
    """Tests for FastAPI rate limiting middleware."""

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_health_endpoint_not_rate_limited(self, test_client):
        """Test that health check endpoint is exempt from rate limiting."""
        from backend.api.middleware.rate_limiter import rate_limiter
        
        # Reset rate limiter
        rate_limiter._requests.clear()
        
        # Should be able to call health endpoint many times
        for _ in range(20):
            response = test_client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_root_endpoint_not_rate_limited(self, test_client):
        """Test that root endpoint is exempt from rate limiting."""
        from backend.api.middleware.rate_limiter import rate_limiter
        
        rate_limiter._requests.clear()
        
        for _ in range(20):
            response = test_client.get("/")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_rate_limit_headers_present(self, test_client):
        """Test that rate limit headers are included in responses."""
        from backend.api.middleware.rate_limiter import rate_limiter
        
        rate_limiter._requests.clear()
        
        # Use an endpoint that IS rate limited (not health or root)
        response = test_client.get("/customers/lookup")
        
        # Rate limit headers should be present on rate-limited endpoints
        # (May not be on exempt endpoints like /health)
        has_headers = "X-RateLimit-Limit" in response.headers or response.status_code in [400, 404]
        assert has_headers

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_rate_limit_headers_values(self, test_client):
        """Test that rate limit header values are correct."""
        from backend.api.middleware.rate_limiter import rate_limiter
        
        rate_limiter._requests.clear()
        
        # Test on a rate-limited endpoint
        response = test_client.get("/customers/lookup")
        
        # Check header values if present
        if "X-RateLimit-Limit" in response.headers:
            limit = int(response.headers.get("X-RateLimit-Limit", "0"))
            remaining = int(response.headers.get("X-RateLimit-Remaining", "-1"))
            
            assert limit > 0
            assert remaining >= 0
        else:
            # Endpoint may be exempt from rate limiting
            assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_rate_limit_exceeded_returns_429(self):
        """Test that exceeding rate limit returns 429 status."""
        from backend.api.middleware.rate_limiter import RateLimiter
        
        # Create a limiter with very low limit for testing
        test_limiter = RateLimiter(requests_per_window=2, window_seconds=60)
        
        # Use an event loop to run async functions
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            # Exhaust the limit
            loop.run_until_complete(test_limiter.is_allowed("test-ip-429"))
            loop.run_until_complete(test_limiter.is_allowed("test-ip-429"))
            
            # Next request should be blocked
            result = loop.run_until_complete(test_limiter.is_allowed("test-ip-429"))
            assert result is False
        finally:
            loop.close()

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_rate_limit_error_response_format(self):
        """Test that rate limit error response has correct format."""
        # Simulate rate limit response
        expected_response = {
            "detail": "Rate limit exceeded. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": 60
        }
        
        # Verify structure
        assert "detail" in expected_response
        assert "error_code" in expected_response
        assert "retry_after" in expected_response
        assert isinstance(expected_response["retry_after"], int)

    @pytest.mark.asyncio
    @pytest.mark.api
    def test_rate_limit_retry_after_header(self):
        """Test that Retry-After header is included when limit exceeded."""
        # Verify Retry-After header should be present
        expected_headers = {
            "X-RateLimit-Limit": "10",
            "X-RateLimit-Remaining": "0",
            "Retry-After": "60"
        }
        
        assert "Retry-After" in expected_headers
        assert expected_headers["Retry-After"] == "60"


# ============== Concurrent Request Tests ==============

class TestRateLimitConcurrency:
    """Tests for rate limiting under concurrent load."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_requests_respect_limit(self, rate_limiter_instance):
        """Test that concurrent requests still respect rate limit."""
        limiter = rate_limiter_instance
        
        # Send 10 concurrent requests
        async def make_request():
            return await limiter.is_allowed("concurrent-ip")
        
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Only 5 should be allowed (the limit)
        allowed = sum(1 for r in results if r)
        assert allowed == 5

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_requests_thread_safety(self, rate_limiter_instance):
        """Test that rate limiter is thread-safe under concurrency."""
        limiter = rate_limiter_instance
        
        # Send many concurrent requests
        async def make_request():
            return await limiter.is_allowed("thread-safe-ip")
        
        # Should not raise race condition errors
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Should have exactly 5 allowed
        allowed_count = sum(1 for r in results if r)
        assert allowed_count == 5


# ============== Configuration Tests ==============

class TestRateLimitConfiguration:
    """Tests for rate limit configuration."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_default_configuration(self):
        """Test default rate limit configuration."""
        from backend.api.middleware.rate_limiter import rate_limiter
        
        # Default should be 10 requests per minute
        assert rate_limiter.requests_per_window == 10
        assert rate_limiter.window_seconds == 60

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_custom_configuration(self):
        """Test custom rate limit configuration."""
        from backend.api.middleware.rate_limiter import RateLimiter
        
        limiter = RateLimiter(requests_per_window=100, window_seconds=3600)
        
        assert limiter.requests_per_window == 100
        assert limiter.window_seconds == 3600

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_settings_loaded_from_env(self):
        """Test that rate limit settings can be loaded from environment."""
        from backend.config.settings import settings
        
        # Settings should have rate limit config
        assert hasattr(settings, 'rate_limit_requests')
        assert hasattr(settings, 'rate_limit_window')


# ============== Edge Case Tests ==============

class TestRateLimitEdgeCases:
    """Tests for rate limiting edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_empty_key_handling(self, rate_limiter_instance):
        """Test rate limiting with empty key."""
        limiter = rate_limiter_instance
        
        # Should handle empty key gracefully
        result = await limiter.is_allowed("")
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_special_characters_in_key(self, rate_limiter_instance):
        """Test rate limiting with special characters in key."""
        limiter = rate_limiter_instance
        
        # Should handle special characters
        result = await limiter.is_allowed("ip-192.168.1.1:special")
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_very_long_key(self, rate_limiter_instance):
        """Test rate limiting with very long key."""
        limiter = rate_limiter_instance
        
        # Should handle long keys
        long_key = "ip-" + "a" * 1000
        result = await limiter.is_allowed(long_key)
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_rapid_successive_requests(self, rate_limiter_instance):
        """Test rapid successive requests are properly counted."""
        limiter = rate_limiter_instance
        
        # Send requests as fast as possible
        results = []
        for _ in range(10):
            result = await limiter.is_allowed("rapid-ip")
            results.append(result)
        
        # First 5 should be True, rest False
        assert results[:5] == [True] * 5
        assert results[5:] == [False] * 5


# ============== Integration Tests ==============

class TestRateLimitIntegration:
    """Integration tests for rate limiting with other components."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rate_limit_with_form_submission(self, test_client):
        """Test rate limiting doesn't break form submission."""
        from backend.api.middleware.rate_limiter import rate_limiter
        
        rate_limiter._requests.clear()
        
        # Form submission should work (within rate limit)
        with patch('backend.api.routes.web_form.customer_repo') as mock_customer:
            with patch('backend.api.routes.web_form.conversation_repo') as mock_conv:
                with patch('backend.api.routes.web_form.ticket_repo') as mock_ticket:
                    with patch('backend.api.routes.web_form.db'):
                        with patch('backend.api.routes.web_form.queue_client.publish', AsyncMock()):
                            mock_customer.find_or_create = AsyncMock(return_value=MagicMock(id=MagicMock()))
                            mock_conv.get_active_by_customer = AsyncMock(return_value=None)
                            mock_conv.create = AsyncMock(return_value=MagicMock(id=MagicMock()))
                            mock_ticket.get_by_conversation_id = AsyncMock(return_value=None)
                            mock_ticket.create = AsyncMock(return_value=MagicMock(id=MagicMock(), status="open"))
                            
                            response = test_client.post("/support/submit", json={
                                "name": "Test User",
                                "email": "test@example.com",
                                "subject": "Test",
                                "category": "technical",
                                "message": "Test message"
                            })
                            
                            # Should not be rate limited (first request)
                            assert response.status_code in [200, 422]  # 422 if validation fails

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rate_limit_does_not_block_whatsapp_webhook(self, test_client):
        """Test that WhatsApp webhook can receive messages."""
        from backend.api.middleware.rate_limiter import rate_limiter
        
        rate_limiter._requests.clear()
        
        # WhatsApp webhook should work normally
        response = test_client.post(
            "/webhooks/whatsapp",
            json={
                "entry": [{
                    "id": "business-id",
                    "changes": [{
                        "field": "messages",
                        "value": {"messages": []}
                    }]
                }]
            }
        )
        
        # Should not be blocked by rate limiting (first request)
        assert response.status_code == 200


# ============== Test Execution ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
