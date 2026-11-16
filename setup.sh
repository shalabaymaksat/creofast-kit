#!/bin/bash
# Бұлттағы Claude Code сессиясында бір рет: ffmpeg + Python кітапханалары
set -e
if ! command -v ffmpeg >/dev/null; then
  (sudo -n true 2>/dev/null && SUDO=sudo) || SUDO=
  $SUDO apt-get update -qq && $SUDO apt-get install -y -qq ffmpeg >/dev/null
fi
python3 -m pip install -q --disable-pip-version-check numpy pillow requests mediapipe 2>&1 | tail -2 || true
python3 -c "import mediapipe, PIL, numpy, requests; print('setup OK')"
ffmpeg -version | head -1
[ -n "$GROQ_API_KEY" ] && echo "GROQ_API_KEY бар" || echo "!! GROQ_API_KEY жоқ — environment settings-ке қос"
