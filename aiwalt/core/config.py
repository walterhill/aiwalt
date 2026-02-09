"""Centralized configuration loaded from environment variables / .env file."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_PROJECT_ROOT / ".env", _PROJECT_ROOT / "config" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure Speech Services
    azure_speech_key: str = Field(description="Azure Speech Services subscription key")
    azure_speech_region: str = Field(default="eastus", description="Azure region")

    # Anthropic
    anthropic_api_key: str = Field(description="Anthropic API key for Claude")

    # Picovoice / Porcupine
    picovoice_access_key: str = Field(description="Picovoice access key for wake word")

    # Assistant personality
    assistant_name: str = Field(default="Griot", description="Name the assistant responds to")
    wake_word: str = Field(
        default="jarvis",
        description="Built-in Porcupine wake word (jarvis, alexa, computer, hey google, etc.)",
    )

    # Azure TTS voice
    voice_name: str = Field(
        default="en-US-GuyNeural",
        description="Azure TTS voice name",
    )

    # Audio behaviour
    silence_timeout_ms: int = Field(
        default=1500,
        description="Milliseconds of silence before ending speech capture",
    )

    # Conversation
    conversation_history_limit: int = Field(
        default=20,
        description="Max number of message pairs to keep in conversation memory",
    )
    claude_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use",
    )

    # Logging
    log_level: str = Field(default="INFO")


def load_settings() -> Settings:
    """Load and return validated settings."""
    return Settings()  # type: ignore[call-arg]
