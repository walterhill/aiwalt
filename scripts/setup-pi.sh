#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# AIWalt — Raspberry Pi 5 setup script
#
# Run this once on a fresh Raspberry Pi OS (Bookworm, 64-bit) to install
# all system-level dependencies and create a Python virtual environment.
#
# Usage:  chmod +x scripts/setup-pi.sh && ./scripts/setup-pi.sh
# ---------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== AIWalt — Raspberry Pi 5 Setup ==="
echo "Project directory: $PROJECT_DIR"

# ------------------------------------------------------------------
# 1. System packages
# ------------------------------------------------------------------
echo ""
echo "[1/5] Installing system dependencies …"
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    libssl-dev \
    libffi-dev \
    alsa-utils \
    pulseaudio

# ------------------------------------------------------------------
# 2. Verify audio devices
# ------------------------------------------------------------------
echo ""
echo "[2/5] Checking audio devices …"
echo "Recording devices:"
arecord -l 2>/dev/null || echo "  (none found — you may need a USB mic)"
echo ""
echo "Playback devices:"
aplay -l 2>/dev/null || echo "  (none found — check speaker connection)"

# ------------------------------------------------------------------
# 3. Create virtual environment
# ------------------------------------------------------------------
VENV_DIR="$PROJECT_DIR/.venv"
echo ""
echo "[3/5] Creating Python virtual environment at $VENV_DIR …"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# ------------------------------------------------------------------
# 4. Install Python dependencies
# ------------------------------------------------------------------
echo ""
echo "[4/5] Installing Python packages …"
pip install --upgrade pip setuptools wheel
pip install -e "$PROJECT_DIR"

# ------------------------------------------------------------------
# 5. Environment file
# ------------------------------------------------------------------
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "[5/5] Creating .env from template …"
    cp "$PROJECT_DIR/config/.env.example" "$ENV_FILE"
    echo "  Created $ENV_FILE — edit it with your API keys before running."
else
    echo ""
    echo "[5/5] .env already exists, skipping."
fi

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit $ENV_FILE with your API keys"
echo "  2. Activate the venv:  source $VENV_DIR/bin/activate"
echo "  3. Test audio:         aiwalt --list-devices"
echo "  4. Test TTS:           aiwalt --test-tts 'Hello, I am Griot.'"
echo "  5. Test STT:           aiwalt --test-stt"
echo "  6. Run the assistant:  aiwalt"
echo ""
echo "To run as a system service, install the systemd unit:"
echo "  sudo cp scripts/aiwalt.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now aiwalt"
