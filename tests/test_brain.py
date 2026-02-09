"""Tests for the conversation engine."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aiwalt.ai.brain import ConversationEngine, ConversationMessage


def _make_engine(**kwargs) -> ConversationEngine:
    defaults = dict(api_key="test-key", assistant_name="TestBot", max_history=5)
    defaults.update(kwargs)
    engine = ConversationEngine(**defaults)
    return engine


def test_system_prompt_includes_name():
    engine = _make_engine(assistant_name="Griot")
    assert "Griot" in engine.system_prompt


def test_history_trimming():
    engine = _make_engine(max_history=2)
    # Manually add messages exceeding the limit
    for i in range(10):
        engine._history.append(ConversationMessage(role="user", content=f"msg {i}"))
        engine._history.append(ConversationMessage(role="assistant", content=f"reply {i}"))

    engine._trim_history()
    # max_history=2 means 4 messages (2 pairs)
    assert len(engine._history) == 4


def test_reset_clears_history():
    engine = _make_engine()
    engine._history.append(ConversationMessage(role="user", content="hello"))
    engine.reset()
    assert len(engine._history) == 0


@patch("aiwalt.ai.brain.anthropic.Anthropic")
def test_chat_returns_reply(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello from Claude")]
    mock_client.messages.create.return_value = mock_response

    engine = _make_engine()
    engine._client = mock_client

    reply = engine.chat("Hi there")
    assert reply == "Hello from Claude"
    assert len(engine._history) == 2  # user + assistant
    mock_client.messages.create.assert_called_once()
