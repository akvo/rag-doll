#!/usr/bin/env bash
set -eu
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

# alembic upgrade head
uvicorn main:app --reload --port "${BACKEND_PORT}" --host 0.0.0.0
