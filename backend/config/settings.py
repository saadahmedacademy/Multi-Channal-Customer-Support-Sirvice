"""Application settings and configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import secrets
import os

# Get the project root directory (3 levels up from this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection URL"
    )

    # Supabase (optional)
    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL"
    )
    supabase_key: Optional[str] = Field(
        default=None,
        description="Supabase anon key"
    )

    # AI API (Hugging Face)
    huggingface_api_key: Optional[str] = Field(
        default=None,
        description="Hugging Face API key"
    )
    huggingface_model: Optional[str] = Field(
        default="NousResearch/Hermes-3-Llama-3.1-8B",
        description="Hugging Face model to use"
    )

    # WhatsApp (Meta Cloud API)
    meta_whatsapp_token: Optional[str] = Field(
        default=None,
        description="Meta WhatsApp access token"
    )
    meta_whatsapp_phone_id: Optional[str] = Field(
        default=None,
        description="Meta WhatsApp phone ID"
    )
    meta_whatsapp_business_id: Optional[str] = Field(
        default=None,
        description="Meta WhatsApp business ID"
    )
    whatsapp_verify_token: Optional[str] = Field(
        default=None,
        description="WhatsApp webhook verification token"
    )
    whatsapp_app_secret: Optional[str] = Field(
        default=None,
        description="Meta WhatsApp App Secret (for webhook signature verification)"
    )

    # Email (Gmail API)
    gmail_oauth_token: Optional[str] = Field(
        default=None,
        description="Gmail API OAuth token"
    )
    gmail_refresh_token: Optional[str] = Field(
        default=None,
        description="Gmail API OAuth refresh token"
    )
    gmail_client_id: Optional[str] = Field(
        default=None,
        description="Gmail OAuth client ID"
    )
    gmail_client_secret: Optional[str] = Field(
        default=None,
        description="Gmail OAuth client secret"
    )
    gmail_credentials: Optional[str] = Field(
        default=None,
        description="Gmail service account credentials (JSON)"
    )
    gmail_service_account_email: Optional[str] = Field(
        default=None,
        description="Gmail service account email"
    )
    support_email: Optional[str] = Field(
        default=None,
        description="Support email address for sending/receiving"
    )

    # Queue
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka/Redpanda bootstrap servers"
    )

    # Security
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Application secret key"
    )
    internal_api_keys: Optional[str] = Field(
        default="dev-key-12345,admin-key-67890",
        description="Comma-separated list of API keys for internal endpoints"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,https://multi-channal-customer-support-sirv.vercel.app",
        description="Comma-separated list of allowed CORS origins"
    )

    # Rate limiting
    rate_limit_requests: int = Field(
        default=100,
        description="Rate limit requests per window"
    )
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )

    # AI settings
    ai_timeout: int = Field(
        default=30,
        description="AI API timeout in seconds"
    )
    max_tokens: int = Field(
        default=500,
        description="Maximum tokens in AI response"
    )

    # Escalation settings
    escalation_sentiment_threshold: float = Field(
        default=0.3,
        description="Sentiment score threshold for escalation"
    )

    class Config:
        env_file = ENV_FILE_PATH
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def validate(self) -> None:
        """Validate required settings."""
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")

        if self.is_production:
            if not self.whatsapp_verify_token:
                raise ValueError("WHATSAPP_VERIFY_TOKEN is required in production")
            if not self.internal_api_keys:
                raise ValueError("INTERNAL_API_KEYS is required in production")

        if not self.huggingface_api_key:
            raise ValueError("HUGGINGFACE_API_KEY is required")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
