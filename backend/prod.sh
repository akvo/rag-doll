#!/usr/bin/env bash
set -eu
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

# Run the FastAPI server in port 8000
fastapi run main.py
