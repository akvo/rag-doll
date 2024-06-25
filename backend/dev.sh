#!/usr/bin/env bash
set -eu
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

pip -q install --cache-dir=.pip -e /lib/Akvo_rabbitmq_client

alembic upgrade head
uvicorn main:app --reload --port "${BACKEND_PORT}" --host 0.0.0.0