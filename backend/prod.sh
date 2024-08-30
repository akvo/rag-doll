#!/usr/bin/env bash
set -eu

uvicorn main:app --port "${BACKEND_PORT}" --host 0.0.0.0
