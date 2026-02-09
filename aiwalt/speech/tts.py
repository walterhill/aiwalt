"""Text-to-Speech using Azure Cognitive Services Speech SDK."""

from __future__ import annotations

import logging

import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger("aiwalt.tts")


class TextToSpeech:
    """Synthesizes speech from text and plays it through the default speaker."""

    def __init__(
        self,
        azure_key: str,
        azure_region: str,
        voice_name: str = "en-US-GuyNeural",
    ) -> None:
        self._speech_config = speechsdk.SpeechConfig(
            subscription=azure_key,
            region=azure_region,
        )
        self._speech_config.speech_synthesis_voice_name = voice_name

        # Output to the default speaker
        self._audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        self._synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self._speech_config,
            audio_config=self._audio_config,
        )

    def speak(self, text: str) -> bool:
        """Speak the given text aloud. Returns True on success."""
        logger.info("Speaking: %s", text[:80] + ("…" if len(text) > 80 else ""))
        result = self._synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.debug("Speech synthesis completed.")
            return True

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error("Speech synthesis canceled: %s", cancellation.reason)
            if cancellation.reason == speechsdk.CancellationReason.Error:
                logger.error("Error details: %s", cancellation.error_details)
            return False

        return False

    def speak_ssml(self, ssml: str) -> bool:
        """Speak using SSML markup for finer control over prosody, pitch, etc."""
        result = self._synthesizer.speak_ssml_async(ssml).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return True

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error("SSML synthesis canceled: %s", cancellation.error_details)
            return False

        return False
