#!/usr/bin/env bash
set -eu

alembic upgrade head

# get twilio message template
python -m command.get_twilio_message_template

uvicorn main:app --port "${BACKEND_PORT}" --host 0.0.0.0
