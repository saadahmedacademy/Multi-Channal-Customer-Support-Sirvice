"""Unit tests for security headers middleware."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.api.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def app():
    """Create test FastAPI app with security headers."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=False)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/customers/test")
    async def sensitive_endpoint():
        return {"data": "sensitive"}

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_security_headers_present(client):
    """Test that all security headers are present in response."""
    response = client.get("/test")

    assert response.status_code == 200

    # Check all security headers are present
    assert "Content-Security-Policy" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-Content-Type-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Referrer-Policy" in response.headers
    assert "Permissions-Policy" in response.headers
    assert "X-Permitted-Cross-Domain-Policies" in response.headers


def test_x_frame_options(client):
    """Test X-Frame-Options header prevents clickjacking."""
    response = client.get("/test")
    assert response.headers["X-Frame-Options"] == "DENY"


def test_x_content_type_options(client):
    """Test X-Content-Type-Options prevents MIME sniffing."""
    response = client.get("/test")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_x_xss_protection(client):
    """Test X-XSS-Protection header."""
    response = client.get("/test")
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_referrer_policy(client):
    """Test Referrer-Policy header."""
    response = client.get("/test")
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_csp_header(client):
    """Test Content-Security-Policy header."""
    response = client.get("/test")
    csp = response.headers["Content-Security-Policy"]

    # Check key CSP directives
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_permissions_policy(client):
    """Test Permissions-Policy restricts browser features."""
    response = client.get("/test")
    policy = response.headers["Permissions-Policy"]

    # Check restricted features
    assert "geolocation=()" in policy
    assert "microphone=()" in policy
    assert "camera=()" in policy


def test_hsts_not_present_without_https(client):
    """Test HSTS header is not added for HTTP requests."""
    response = client.get("/test")
    # HSTS should not be present for HTTP (enable_hsts=False in fixture)
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_present_with_https():
    """Test HSTS header is added for HTTPS requests."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=True)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app, base_url="https://testserver")
    response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

    # HSTS should be present for HTTPS
    assert "Strict-Transport-Security" in response.headers
    hsts = response.headers["Strict-Transport-Security"]
    assert "max-age=" in hsts
    assert "includeSubDomains" in hsts


def test_cache_control_for_sensitive_endpoints(client):
    """Test Cache-Control headers for sensitive endpoints."""
    response = client.get("/customers/test")

    # Sensitive endpoints should have no-cache headers
    assert "Cache-Control" in response.headers
    assert "no-store" in response.headers["Cache-Control"]
    assert "no-cache" in response.headers["Cache-Control"]
    assert "Pragma" in response.headers
    assert response.headers["Pragma"] == "no-cache"


def test_no_cache_control_for_public_endpoints(client):
    """Test public endpoints don't have strict cache control."""
    response = client.get("/test")

    # Public endpoints should not have strict cache control
    # (or if they do, it should be less restrictive)
    if "Cache-Control" in response.headers:
        assert "no-store" not in response.headers["Cache-Control"]
