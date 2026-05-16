"""Sentry integration for error tracking and performance monitoring."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

from backend.config.settings import settings


def init_sentry():
    """
    Initialize Sentry SDK for error tracking and performance monitoring.

    Only initializes if SENTRY_DSN is configured.
    """
    if not settings.sentry_dsn:
        logging.info("Sentry DSN not configured, skipping Sentry initialization")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,

        # Performance monitoring
        traces_sample_rate=getattr(settings, 'sentry_traces_sample_rate', 0.1),

        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            AsyncioIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],

        # Release tracking
        release=getattr(settings, 'app_version', '1.0.0'),

        # Filter sensitive data
        before_send=filter_sensitive_data,

        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII by default
    )

    logging.info(f"Sentry initialized for environment: {settings.environment}")


def filter_sensitive_data(event, hint):
    """
    Filter sensitive data before sending to Sentry.

    Removes:
    - API keys
    - Passwords
    - Tokens
    - Email addresses (in some contexts)
    """
    # Filter request headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']

        # Remove sensitive headers
        sensitive_headers = [
            'authorization',
            'x-api-key',
            'cookie',
            'x-csrf-token'
        ]

        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[FILTERED]'

    # Filter environment variables
    if 'contexts' in event and 'runtime' in event['contexts']:
        runtime = event['contexts']['runtime']
        if 'env' in runtime:
            env = runtime['env']

            sensitive_env_vars = [
                'DATABASE_URL',
                'OPENROUTER_API_KEY',
                'GEMINI_API_KEY',
                'META_WHATSAPP_TOKEN',
                'GMAIL_CLIENT_SECRET',
                'SECRET_KEY',
                'INTERNAL_API_KEYS'
            ]

            for var in sensitive_env_vars:
                if var in env:
                    env[var] = '[FILTERED]'

    return event


def capture_exception(exception: Exception, context: dict = None):
    """
    Manually capture an exception with additional context.

    Args:
        exception: The exception to capture
        context: Additional context to attach to the event
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_exception(exception)
    else:
        sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", context: dict = None):
    """
    Manually capture a message with additional context.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        context: Additional context to attach to the event
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_context(key, value)
            sentry_sdk.capture_message(message, level=level)
    else:
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: str = None, email: str = None, **kwargs):
    """
    Set user context for error tracking.

    Args:
        user_id: User identifier
        email: User email (will be filtered if PII protection is enabled)
        **kwargs: Additional user attributes
    """
    user_data = {}

    if user_id:
        user_data['id'] = user_id

    if email and not settings.send_default_pii:
        # Hash email for privacy
        import hashlib
        user_data['email_hash'] = hashlib.sha256(email.encode()).hexdigest()[:16]
    elif email:
        user_data['email'] = email

    user_data.update(kwargs)

    sentry_sdk.set_user(user_data)


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: dict = None):
    """
    Add a breadcrumb for debugging context.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "http", "db", "queue")
        level: Severity level
        data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )
