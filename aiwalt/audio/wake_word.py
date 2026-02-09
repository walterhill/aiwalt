"""Wake word detection using Picovoice Porcupine.

Porcupine runs entirely on-device — no cloud calls for the wake word.
Supports built-in keywords: jarvis, alexa, computer, hey google, ok google,
hey siri, porcupine, bumblebee, terminator, etc.
"""

from __future__ import annotations

import logging
from typing import Callable

import pvporcupine
from pvrecorder import PvRecorder

logger = logging.getLogger("aiwalt.wake_word")


class WakeWordDetector:
    """Listens continuously for a wake word and fires a callback when detected."""

    def __init__(
        self,
        access_key: str,
        keyword: str = "jarvis",
        sensitivity: float = 0.6,
        audio_device_index: int = -1,
    ) -> None:
        self._access_key = access_key
        self._keyword = keyword
        self._sensitivity = sensitivity
        self._audio_device_index = audio_device_index
        self._porcupine: pvporcupine.Porcupine | None = None
        self._recorder: PvRecorder | None = None
        self._running = False

    def start(self, on_wake: Callable[[], None]) -> None:
        """Block and listen for the wake word. Calls *on_wake* each time it's detected."""
        self._porcupine = pvporcupine.create(
            access_key=self._access_key,
            keywords=[self._keyword],
            sensitivities=[self._sensitivity],
        )
        self._recorder = PvRecorder(
            frame_length=self._porcupine.frame_length,
            device_index=self._audio_device_index,
        )
        self._recorder.start()
        self._running = True

        logger.info(
            "Listening for wake word '%s' … (sensitivity=%.2f)",
            self._keyword,
            self._sensitivity,
        )

        try:
            while self._running:
                pcm = self._recorder.read()
                result = self._porcupine.process(pcm)
                if result >= 0:
                    logger.info("Wake word detected!")
                    on_wake()
        except KeyboardInterrupt:
            logger.info("Wake word listener stopped by user.")
        finally:
            self.stop()

    def stop(self) -> None:
        """Release resources."""
        self._running = False
        if self._recorder is not None:
            self._recorder.stop()
            self._recorder.delete()
            self._recorder = None
        if self._porcupine is not None:
            self._porcupine.delete()
            self._porcupine = None

    @staticmethod
    def list_audio_devices() -> list[str]:
        """Return available audio input devices (useful for debugging on Pi)."""
        return PvRecorder.get_available_devices()
