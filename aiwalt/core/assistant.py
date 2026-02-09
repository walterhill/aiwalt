"""Main assistant orchestrator — ties wake word, STT, brain, and TTS together."""

from __future__ import annotations

import logging
import threading
import time

from aiwalt.ai.brain import ConversationEngine
from aiwalt.audio.wake_word import WakeWordDetector
from aiwalt.core.config import Settings
from aiwalt.speech.stt import SpeechToText
from aiwalt.speech.tts import TextToSpeech

logger = logging.getLogger("aiwalt.assistant")


class Assistant:
    """The main event loop for the voice assistant.

    Flow:
      1. Wait for wake word (on-device, Porcupine)
      2. Play acknowledgement chime / speak short prompt
      3. Capture speech via Azure STT
      4. Send transcription to Claude
      5. Speak Claude's reply via Azure TTS
      6. Return to step 1
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        self._wake = WakeWordDetector(
            access_key=settings.picovoice_access_key,
            keyword=settings.wake_word,
        )
        self._stt = SpeechToText(
            azure_key=settings.azure_speech_key,
            azure_region=settings.azure_speech_region,
            silence_timeout_ms=settings.silence_timeout_ms,
        )
        self._tts = TextToSpeech(
            azure_key=settings.azure_speech_key,
            azure_region=settings.azure_speech_region,
            voice_name=settings.voice_name,
        )
        self._brain = ConversationEngine(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
            assistant_name=settings.assistant_name,
            max_history=settings.conversation_history_limit,
        )

        self._interaction_lock = threading.Lock()
        self._running = False

    def run(self) -> None:
        """Start the assistant. Blocks until interrupted."""
        self._running = True
        logger.info(
            "Starting %s — wake word: '%s'",
            self._settings.assistant_name,
            self._settings.wake_word,
        )
        logger.info("Say '%s' to begin …", self._settings.wake_word)

        try:
            self._wake.start(on_wake=self._handle_wake)
        except KeyboardInterrupt:
            logger.info("Shutting down …")
        finally:
            self.shutdown()

    def _handle_wake(self) -> None:
        """Called by the wake-word detector when the keyword is heard."""
        if not self._interaction_lock.acquire(blocking=False):
            logger.debug("Already handling an interaction, skipping.")
            return

        try:
            # Stop the wake word recorder so the mic is free for Azure STT
            self._wake.stop()

            # Acknowledge the wake word
            self._tts.speak("Yes?")

            # Listen for the user's command
            result = self._stt.recognize_once()

            if not result.success or not result.text.strip():
                self._tts.speak("I didn't catch that.")
                self._restart_wake_listener()
                return

            user_text = result.text.strip()
            logger.info("User said: %s", user_text)

            # Check for exit commands
            if self._is_exit_command(user_text):
                self._tts.speak("Goodbye!")
                self._running = False
                return

            # Check for reset command
            if self._is_reset_command(user_text):
                self._brain.reset()
                self._tts.speak("Conversation history cleared. Fresh start!")
                self._restart_wake_listener()
                return

            # Get Claude's response
            reply = self._brain.chat(user_text)

            # Speak the response
            self._tts.speak(reply)

            # Go back to listening for wake word
            self._restart_wake_listener()

        except Exception:
            logger.exception("Error during interaction")
            try:
                self._tts.speak("I ran into an error. Let me reset.")
            except Exception:
                pass
            self._restart_wake_listener()
        finally:
            self._interaction_lock.release()

    def _restart_wake_listener(self) -> None:
        """Re-initialize and start the wake word detector in a new thread."""
        if not self._running:
            return

        self._wake = WakeWordDetector(
            access_key=self._settings.picovoice_access_key,
            keyword=self._settings.wake_word,
        )

        # Small delay to let the mic settle
        time.sleep(0.3)

        thread = threading.Thread(
            target=self._wake.start,
            args=(self._handle_wake,),
            daemon=True,
        )
        thread.start()

    def shutdown(self) -> None:
        """Clean up resources."""
        self._running = False
        self._wake.stop()
        logger.info("%s has shut down.", self._settings.assistant_name)

    @staticmethod
    def _is_exit_command(text: str) -> bool:
        exit_phrases = {"goodbye", "shut down", "exit", "quit", "power off", "go to sleep"}
        normalized = text.lower().rstrip(".")
        return normalized in exit_phrases

    @staticmethod
    def _is_reset_command(text: str) -> bool:
        reset_phrases = {"reset conversation", "clear history", "start over", "new conversation"}
        normalized = text.lower().rstrip(".")
        return normalized in reset_phrases
