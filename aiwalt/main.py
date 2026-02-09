"""Entry point for the AIWalt voice assistant."""

from __future__ import annotations

import argparse
import sys

from aiwalt.audio.wake_word import WakeWordDetector
from aiwalt.core.config import load_settings
from aiwalt.utils.logger import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AIWalt — AI voice assistant for Raspberry Pi 5",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit",
    )
    parser.add_argument(
        "--test-tts",
        type=str,
        metavar="TEXT",
        help="Speak the given text and exit (useful for testing Azure TTS)",
    )
    parser.add_argument(
        "--test-stt",
        action="store_true",
        help="Record one utterance, transcribe it, and exit",
    )
    args = parser.parse_args()

    # --- List audio devices (no config needed) ---
    if args.list_devices:
        devices = WakeWordDetector.list_audio_devices()
        print("Available audio input devices:")
        for i, name in enumerate(devices):
            print(f"  [{i}] {name}")
        sys.exit(0)

    # --- Load settings ---
    try:
        settings = load_settings()
    except Exception as exc:
        print(f"Failed to load configuration: {exc}", file=sys.stderr)
        print("Make sure you have a .env file — see config/.env.example", file=sys.stderr)
        sys.exit(1)

    logger = setup_logging(settings.log_level)

    # --- Test TTS ---
    if args.test_tts:
        from aiwalt.speech.tts import TextToSpeech

        tts = TextToSpeech(
            azure_key=settings.azure_speech_key,
            azure_region=settings.azure_speech_region,
            voice_name=settings.voice_name,
        )
        success = tts.speak(args.test_tts)
        sys.exit(0 if success else 1)

    # --- Test STT ---
    if args.test_stt:
        from aiwalt.speech.stt import SpeechToText

        stt = SpeechToText(
            azure_key=settings.azure_speech_key,
            azure_region=settings.azure_speech_region,
            silence_timeout_ms=settings.silence_timeout_ms,
        )
        result = stt.recognize_once()
        if result.success:
            print(f"Transcription: {result.text}")
        else:
            print(f"Recognition failed: {result.reason}")
        sys.exit(0 if result.success else 1)

    # --- Run the full assistant ---
    from aiwalt.core.assistant import Assistant

    logger.info("Initializing %s …", settings.assistant_name)
    assistant = Assistant(settings)
    assistant.run()


if __name__ == "__main__":
    main()
