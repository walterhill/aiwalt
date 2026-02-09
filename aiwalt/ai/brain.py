"""Conversation engine powered by Claude (Anthropic API).

Maintains a rolling conversation history so the assistant feels coherent
across multiple exchanges within a session.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import anthropic

logger = logging.getLogger("aiwalt.brain")

SYSTEM_PROMPT = """\
You are {name}, an advanced AI voice assistant running on a Raspberry Pi.
You are inspired by Jarvis and Griot from the Marvel universe — brilliant, \
warm, articulate, and occasionally witty.

Guidelines:
- Keep responses concise and conversational — they will be spoken aloud.
- Aim for 1-3 sentences unless the user explicitly asks for detail.
- Use natural, spoken-English phrasing (avoid bullet lists, markdown, or code blocks \
unless the user specifically asks for them).
- If the user asks you to remember something, acknowledge it and weave it into context.
- You may address the user respectfully; feel free to develop personality over time.
- If you don't know something, say so honestly.
"""


@dataclass
class ConversationMessage:
    role: str  # "user" or "assistant"
    content: str


@dataclass
class ConversationEngine:
    """Stateful conversation engine backed by Claude."""

    api_key: str
    model: str = "claude-sonnet-4-20250514"
    assistant_name: str = "Griot"
    max_history: int = 20
    _history: list[ConversationMessage] = field(default_factory=list)
    _client: anthropic.Anthropic | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=self.api_key)

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(name=self.assistant_name)

    def chat(self, user_text: str) -> str:
        """Send *user_text* to Claude and return the assistant's reply."""
        self._history.append(ConversationMessage(role="user", content=user_text))
        self._trim_history()

        messages = [{"role": m.role, "content": m.content} for m in self._history]

        logger.debug("Sending %d messages to Claude (%s)", len(messages), self.model)

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=512,
                system=self.system_prompt,
                messages=messages,
            )
            reply = response.content[0].text
        except anthropic.APIError as exc:
            logger.error("Claude API error: %s", exc)
            reply = "I'm sorry, I had trouble reaching my brain just now. Could you try again?"

        self._history.append(ConversationMessage(role="assistant", content=reply))
        logger.info("Claude replied: %s", reply[:120])
        return reply

    def reset(self) -> None:
        """Clear conversation history."""
        self._history.clear()
        logger.info("Conversation history cleared.")

    def _trim_history(self) -> None:
        """Keep only the most recent message pairs to stay within context limits."""
        max_messages = self.max_history * 2  # pairs of user + assistant
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]
