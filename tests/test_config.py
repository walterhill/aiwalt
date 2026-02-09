"""Tests for configuration loading."""

from __future__ import annotations

import os
from unittest.mock import patch

from aiwalt.core.config import Settings


def _make_env(**overrides: str) -> dict[str, str]:
    """Return a minimal valid environment dict for Settings."""
    base = {
        "AZURE_SPEECH_KEY": "test-azure-key",
        "AZURE_SPEECH_REGION": "eastus",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "PICOVOICE_ACCESS_KEY": "test-picovoice-key",
    }
    base.update(overrides)
    return base


def test_settings_defaults():
    env = _make_env()
    with patch.dict(os.environ, env, clear=False):
        s = Settings(**env)
    assert s.assistant_name == "Griot"
    assert s.wake_word == "jarvis"
    assert s.voice_name == "en-US-GuyNeural"
    assert s.silence_timeout_ms == 1500
    assert s.conversation_history_limit == 20


def test_settings_custom_values():
    env = _make_env(
        ASSISTANT_NAME="Friday",
        WAKE_WORD="computer",
        VOICE_NAME="en-US-JennyNeural",
        SILENCE_TIMEOUT_MS="2000",
    )
    with patch.dict(os.environ, env, clear=False):
        s = Settings(**env)
    assert s.assistant_name == "Friday"
    assert s.wake_word == "computer"
    assert s.voice_name == "en-US-JennyNeural"
    assert s.silence_timeout_ms == 2000
