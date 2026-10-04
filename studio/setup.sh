#!/usr/bin/env bash
# One-time setup for a fresh session: python deps, ffmpeg check, Kokoro voice model (from GitHub releases).
set -e
pip install --quiet --break-system-packages kokoro-onnx soundfile numpy pillow 2>&1 | tail -1 || true
command -v ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
mkdir -p ~/kokoro && cd ~/kokoro
B=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s kokoro-v1.0.onnx ] || curl -sSL -o kokoro-v1.0.onnx $B/kokoro-v1.0.onnx
[ -s voices-v1.0.bin ] || curl -sSL -o voices-v1.0.bin $B/voices-v1.0.bin
ls -la ~/kokoro
fc-list | grep -c Poppins || echo "WARNING: Poppins font missing (renderer falls back to DejaVu, looks worse)"
