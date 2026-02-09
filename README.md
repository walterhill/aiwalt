# AIWalt

A voice-activated AI assistant for **Raspberry Pi 5** — inspired by Jarvis and Griot from the Marvel universe. Always listening, always ready.

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Wake Word   │────▶│  Speech to   │────▶│    Claude     │────▶│  Text to     │
│  (Porcupine) │     │  Text (Azure)│     │    (Brain)    │     │  Speech(Azure)│
│  ON-DEVICE   │     │              │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     🎤 Mic              🎤 → 📝              📝 → 🧠              🔊 Speaker
```

1. **Wake word detection** — Porcupine (Picovoice) listens continuously on-device. No cloud calls, no latency. Default wake word: `"jarvis"`.
2. **Speech-to-Text** — Azure Cognitive Services transcribes your voice command.
3. **AI Brain** — Claude (Anthropic) processes the transcription with conversational memory.
4. **Text-to-Speech** — Azure synthesizes the response and plays it through your speaker.

## Prerequisites

### Hardware
- Raspberry Pi 5 (4GB+ RAM recommended)
- USB microphone or a HAT with mic (e.g., ReSpeaker)
- Speaker (3.5mm, Bluetooth, or USB)
- Internet connection (for Azure + Claude APIs)

### API Keys (3 required)
| Service | Purpose | Get it at |
|---------|---------|-----------|
| **Picovoice** | Wake word detection | https://console.picovoice.ai/ |
| **Azure Speech** | STT + TTS | https://portal.azure.com/ → Cognitive Services → Speech |
| **Anthropic** | AI conversation | https://console.anthropic.com/ |

## Quick Start

### 1. Clone and set up

```bash
git clone <this-repo> ~/aiwalt
cd ~/aiwalt
chmod +x scripts/setup-pi.sh
./scripts/setup-pi.sh
```

The setup script installs system dependencies, creates a Python virtual environment, and installs the package.

### 2. Configure API keys

```bash
cp config/.env.example .env
nano .env   # fill in your 3 API keys
```

### 3. Test components individually

```bash
source .venv/bin/activate

# List audio devices (verify your mic is detected)
aiwalt --list-devices

# Test text-to-speech
aiwalt --test-tts "Hello, I am Griot. Your AI assistant is online."

# Test speech-to-text (speak after running)
aiwalt --test-stt
```

### 4. Run the assistant

```bash
aiwalt
```

Say **"Jarvis"** (or your configured wake word), then speak your command.

## Run as a 24/7 Service

```bash
# Copy the systemd unit (edit paths in the file if your user isn't 'pi')
sudo cp scripts/aiwalt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aiwalt

# View logs
journalctl -u aiwalt -f
```

## Configuration

All settings are configured via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_SPEECH_KEY` | *(required)* | Azure Speech Services key |
| `AZURE_SPEECH_REGION` | `eastus` | Azure region |
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key |
| `PICOVOICE_ACCESS_KEY` | *(required)* | Picovoice access key |
| `ASSISTANT_NAME` | `Griot` | Name used in the system prompt |
| `WAKE_WORD` | `jarvis` | Porcupine built-in keyword |
| `VOICE_NAME` | `en-US-GuyNeural` | Azure TTS voice |
| `SILENCE_TIMEOUT_MS` | `1500` | Silence before ending speech capture |
| `CONVERSATION_HISTORY_LIMIT` | `20` | Max conversation pairs to remember |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model identifier |

### Available Wake Words (built-in)

`alexa`, `bumblebee`, `computer`, `hey google`, `hey siri`, `jarvis`, `ok google`, `porcupine`, `terminator`

### Recommended Azure TTS Voices

- `en-US-GuyNeural` — deep, confident male voice (Jarvis-like)
- `en-US-DavisNeural` — warm, authoritative male voice
- `en-US-JennyNeural` — clear female voice (Friday-like)
- `en-US-AriaNeural` — expressive female voice

## Voice Commands

- Say the **wake word** to activate, then speak naturally
- Say **"goodbye"** / **"shut down"** to stop the assistant
- Say **"reset conversation"** / **"start over"** to clear chat history

## Project Structure

```
aiwalt/
├── aiwalt/
│   ├── main.py              # CLI entry point
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   └── assistant.py      # Main orchestrator
│   ├── audio/
│   │   └── wake_word.py      # Porcupine wake word detector
│   ├── speech/
│   │   ├── stt.py            # Azure Speech-to-Text
│   │   └── tts.py            # Azure Text-to-Speech
│   ├── ai/
│   │   └── brain.py          # Claude conversation engine
│   └── utils/
│       └── logger.py         # Logging setup
├── config/
│   └── .env.example          # Template for API keys
├── scripts/
│   ├── setup-pi.sh           # One-time Pi setup
│   └── aiwalt.service        # systemd unit file
├── tests/
├── pyproject.toml
└── requirements.txt
```

## Troubleshooting

**No audio devices found**: Make sure your USB mic is plugged in. Run `arecord -l` and `aplay -l` to verify. You may need to set the default device in `/etc/asound.conf` or PulseAudio config.

**Wake word not triggering**: Try increasing sensitivity by modifying `WakeWordDetector(sensitivity=0.7)` or running in a quieter environment.

**Azure STT returns no match**: Check your Azure key/region, and ensure the mic is picking up audio (`arecord -d 3 test.wav && aplay test.wav`).

**Service won't start**: Check `journalctl -u aiwalt -e` for errors. Ensure the `.env` file is readable and paths in `aiwalt.service` match your setup.
