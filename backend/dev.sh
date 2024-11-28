#!/usr/bin/env bash
set -eu

# Install FFmpeg to support pydub
# apt-get update
# apt-get install -y flac ffmpeg
# apt-get clean
# rm -rf /var/lib/apt/lists/*

pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

pip -q install --cache-dir=.pip -e /lib/Akvo_rabbitmq_client

alembic upgrade head

# get twilio message template
python -m command.get_twilio_message_template

uvicorn main:app --reload --port "${BACKEND_PORT}" --host 0.0.0.0
