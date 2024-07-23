#!/usr/bin/env bash
set -eu

# Install FFmpeg to support pydub
apt-get update
apt-get install -y ffmpeg
apt-get clean
rm -rf /var/lib/apt/lists/*

pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

uvicorn main:app --port "${BACKEND_PORT}" --host 0.0.0.0
