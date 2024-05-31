#!/usr/bin/env bash
set -eu
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

# Run the FastAPI server in port 5000, only accessible from docker network
fastapi run main.py
