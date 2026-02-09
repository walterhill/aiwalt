"""Speech-to-Text using Azure Cognitive Services Speech SDK."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger("aiwalt.stt")


@dataclass
class TranscriptionResult:
    text: str
    success: bool
    reason: str = ""


class SpeechToText:
    """Captures audio from the default microphone and returns a transcription."""

    def __init__(
        self,
        azure_key: str,
        azure_region: str,
        language: str = "en-US",
        silence_timeout_ms: int = 1500,
    ) -> None:
        self._speech_config = speechsdk.SpeechConfig(
            subscription=azure_key,
            region=azure_region,
        )
        self._speech_config.speech_recognition_language = language

        # Auto-detect end-of-speech after silence
        self._speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
            str(silence_timeout_ms),
        )
        self._speech_config.set_property(
            speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
            str(silence_timeout_ms),
        )

    def recognize_once(self) -> TranscriptionResult:
        """Record from the microphone until speech ends and return the transcript.

        Uses single-shot recognition which automatically stops after one utterance.
        """
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self._speech_config,
            audio_config=audio_config,
        )

        logger.info("Listening for speech …")
        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logger.info("Transcribed: %s", result.text)
            return TranscriptionResult(text=result.text, success=True)

        if result.reason == speechsdk.ResultReason.NoMatch:
            detail = result.no_match_details
            logger.warning("No speech recognized: %s", detail)
            return TranscriptionResult(text="", success=False, reason="no_match")

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error("Recognition canceled: %s", cancellation.reason)
            if cancellation.reason == speechsdk.CancellationReason.Error:
                logger.error("Error details: %s", cancellation.error_details)
            return TranscriptionResult(
                text="", success=False, reason=f"canceled: {cancellation.reason}"
            )

        return TranscriptionResult(text="", success=False, reason="unknown")
