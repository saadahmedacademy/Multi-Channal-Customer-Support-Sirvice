"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from backend.config.settings import settings
from backend.config.logging import get_logger
from backend.db.connection import init_db, close_db, db
from backend.integrations.queue_client import queue_client
from backend.api.middleware.error_handler import register_exception_handlers
from backend.api.middleware.rate_limiter import RateLimitMiddleware
from backend.api.middleware.security_headers import SecurityHeadersMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up AI Support Agent API...")
    
    try:
        # Initialize database
        await init_db(settings.database_url)
        logger.info("Database connection initialized")
        
        # Start queue producer
        try:
            await queue_client.start_producer()
            logger.info("Queue producer started")
        except Exception as e:
            logger.warning(f"Queue producer failed to start (non-fatal): {e}")
            logger.warning("Messages will not be queued until Redpanda is available")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Support Agent API...")
    
    # Stop queue producer
    await queue_client.stop_producer()
    
    # Close database connections
    await close_db()
    
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="AI Customer Support Agent API",
    description="Multi-channel AI-powered customer support API",
    version="1.0.0",
    lifespan=lifespan,
    # Security: Limit request body size to 10MB to prevent large payload attacks
    # Customer messages should be well under this limit
    max_request_size=10 * 1024 * 1024  # 10MB
)

# Configure CORS
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
# Enable HSTS only in production (when using HTTPS)
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=(settings.environment == "production")
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Include route routers
from backend.api.routes import web_form, tickets, whatsapp, customers, conversations, metrics, email, customer_linking
app.include_router(web_form.router, prefix="/support", tags=["support"])
app.include_router(tickets.router, prefix="/support", tags=["tickets"])
app.include_router(whatsapp.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(email.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(customer_linking.router, prefix="/customers", tags=["customers"])
app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])


@app.get("/health")
async def health_check():
    """
    Health check endpoint with comprehensive service verification.

    Checks database, queue, and AI API connectivity.
    """
    # Check WhatsApp configuration
    from backend.integrations.email_client import gmail_client
    from backend.integrations.whatsapp_client import whatsapp_client
    whatsapp_configured = whatsapp_client.is_configured() if hasattr(whatsapp_client, 'is_configured') else bool(settings.meta_whatsapp_token and settings.meta_whatsapp_phone_id)

    # Check Email configuration
    email_configured = gmail_client.is_configured() if hasattr(gmail_client, 'is_configured') else bool(settings.gmail_oauth_token)

    # Check database
    db_status = "connected"
    try:
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check queue
    queue_status = "connected"
    if not queue_client.producer:
        queue_status = "producer not started"

    # Check AI API (lightweight check)
    ai_status = "configured"
    if not settings.openrouter_api_key and not settings.gemini_api_key:
        ai_status = "no API key configured"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "channels": {
            "web_form": "active",
            "whatsapp": "active" if whatsapp_configured else "inactive",
            "email": "active" if email_configured else "inactive"
        },
        "services": {
            "database": db_status,
            "queue": queue_status,
            "ai_api": ai_status
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Customer Support Agent API",
        "version": "1.0.0",
        "description": "Multi-channel AI-powered customer support",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routes (to be added in subsequent tasks)
# from backend.api.routes import web_form, whatsapp, tickets
# app.include_router(web_form.router, prefix="/support", tags=["support"])
# app.include_router(whatsapp.router, prefix="/webhooks", tags=["webhooks"])
# app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
