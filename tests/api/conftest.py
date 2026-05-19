"""Pytest configuration for API tests."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test to avoid rate limit errors."""
    from backend.api.middleware.rate_limiter import rate_limiter

    # Clear rate limiter state before each test
    rate_limiter._requests.clear()

    yield

    # Clean up after test
    rate_limiter._requests.clear()


@pytest.fixture
def test_client():
    """Create test client with rate limiting reset."""
    return TestClient(app)
