#!/usr/bin/env bash
set -eu

# Install required packages
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

pip -q install --cache-dir=.pip -e /lib/Akvo_rabbitmq_client

# Run Hypercorn with auto-reload
hypercorn main:app --bind 0.0.0.0:$TWILIO_BOT_PORT --reload
