"""
Customer Success FTE — Configuration Management
=================================================
Phase 2: Specialization

Centralized configuration using environment variables with defaults.
All sensitive data comes from environment variables (secrets in K8s).
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "fte_db")
    user: str = os.getenv("POSTGRES_USER", "fte_user")
    password: str = os.getenv("POSTGRES_PASSWORD", "fte_password")
    pool_min_size: int = 2
    pool_max_size: int = 20

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class KafkaConfig:
    """Kafka streaming configuration."""
    bootstrap_servers: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
    )
    group_id: str = os.getenv("KAFKA_GROUP_ID", "fte-message-processor")

    # Topic definitions
    topics = {
        'tickets_incoming': 'fte.tickets.incoming',
        'email_inbound': 'fte.channels.email.inbound',
        'whatsapp_inbound': 'fte.channels.whatsapp.inbound',
        'webform_inbound': 'fte.channels.webform.inbound',
        'email_outbound': 'fte.channels.email.outbound',
        'whatsapp_outbound': 'fte.channels.whatsapp.outbound',
        'escalations': 'fte.escalations',
        'metrics': 'fte.metrics',
        'dlq': 'fte.dlq',
    }


@dataclass
class GmailConfig:
    """Gmail API configuration."""
    enabled: bool = os.getenv("GMAIL_ENABLED", "true").lower() == "true"
    credentials_path: str = os.getenv(
        "GMAIL_CREDENTIALS_PATH", "credentials/gmail.json"
    )
    pubsub_topic: str = os.getenv(
        "GMAIL_PUBSUB_TOPIC", "projects/fte-project/topics/gmail-inbox"
    )
    max_response_length: int = int(
        os.getenv("MAX_EMAIL_LENGTH", "2000")
    )


@dataclass
class WhatsAppConfig:
    """Twilio WhatsApp configuration."""
    enabled: bool = os.getenv("WHATSAPP_ENABLED", "true").lower() == "true"
    account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    whatsapp_number: str = os.getenv(
        "TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"
    )
    max_response_length: int = int(
        os.getenv("MAX_WHATSAPP_LENGTH", "1600")
    )


@dataclass
class WebFormConfig:
    """Web support form configuration."""
    enabled: bool = os.getenv("WEBFORM_ENABLED", "true").lower() == "true"
    max_response_length: int = int(
        os.getenv("MAX_WEBFORM_LENGTH", "1000")
    )
    allowed_origins: list = None  # type: ignore

    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "1024"))
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))


@dataclass
class AgentConfig:
    """Agent behavior configuration."""
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    escalation_sentiment_threshold: float = float(
        os.getenv("ESCALATION_SENTIMENT_THRESHOLD", "0.3")
    )
    conversation_window_hours: int = int(
        os.getenv("CONVERSATION_WINDOW_HOURS", "24")
    )
    max_kb_results: int = int(os.getenv("MAX_KB_RESULTS", "5"))


# ─── Global Config Instance ────────────────────────────────────────────────

db = DatabaseConfig()
kafka = KafkaConfig()
gmail = GmailConfig()
whatsapp = WhatsAppConfig()
webform = WebFormConfig()
openai = OpenAIConfig()
agent = AgentConfig()


def validate_config() -> list[str]:
    """Validate required configuration values. Returns list of errors."""
    errors = []

    if not db.host:
        errors.append("POSTGRES_HOST is required")
    if not db.password:
        errors.append("POSTGRES_PASSWORD is required")
    if not openai.api_key:
        errors.append("OPENAI_API_KEY is required")
    if whatsapp.enabled and not whatsapp.account_sid:
        errors.append("TWILIO_ACCOUNT_SID is required when WhatsApp is enabled")
    if whatsapp.enabled and not whatsapp.auth_token:
        errors.append("TWILIO_AUTH_TOKEN is required when WhatsApp is enabled")

    return errors
