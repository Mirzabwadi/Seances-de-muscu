#!/bin/bash
# Reinstalls the video toolchain (HyperFrames, its render browser, Whisper and the
# background-removal model) on a fresh cloud machine. Each step checks first, so a
# warm machine skips everything in a second or two.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

HYPERFRAMES_VERSION=0.8.221
CACHE="$HOME/.cache/hyperframes"

# Node's fetch ignores HTTPS_PROXY unless told otherwise; HyperFrames downloads models with it.
export NODE_USE_ENV_PROXY=1
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export NODE_USE_ENV_PROXY=1' >> "$CLAUDE_ENV_FILE"
fi

# Everything below reports to stderr so it stays out of the session's context.
exec 1>&2

if [ "$(hyperframes --version 2>/dev/null || true)" != "$HYPERFRAMES_VERSION" ]; then
  echo "Installing hyperframes@$HYPERFRAMES_VERSION"
  npm install -g "hyperframes@$HYPERFRAMES_VERSION"
fi

if ! ls "$CACHE"/chrome/chrome-headless-shell/*/chrome-headless-shell-linux64/chrome-headless-shell >/dev/null 2>&1; then
  echo "Installing the render browser"
  hyperframes browser ensure
fi

warm=$(mktemp -d)
trap 'rm -rf "$warm"' EXIT

# Whisper runtime and the multilingual "medium" model used for French captions:
# a one-second transcription installs both.
if [ ! -x "$CACHE/whisper/whisper.cpp/build/bin/whisper-cli" ] || [ ! -s "$CACHE/whisper/models/ggml-medium.bin" ]; then
  echo "Installing Whisper (runtime + medium model)"
  ffmpeg -loglevel error -y -f lavfi -i "anullsrc=r=16000:cl=mono" -t 1 "$warm/silence.wav"
  hyperframes transcribe "$warm/silence.wav" --dir "$warm" --model medium --language fr --timeout 900000
fi

# Background-removal model and its ONNX runtime: one tiny image installs both.
if [ -z "$(ls -A "$CACHE/background-removal/models" 2>/dev/null)" ] || [ -z "$(ls -A "$CACHE/optional" 2>/dev/null)" ]; then
  echo "Installing the background-removal model"
  ffmpeg -loglevel error -y -f lavfi -i "color=c=gray:s=64x64" -frames:v 1 "$warm/probe.png"
  hyperframes remove-background "$warm/probe.png" -o "$warm/probe-cutout.png"
fi
