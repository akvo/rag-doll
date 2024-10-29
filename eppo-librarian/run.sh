#!/usr/bin/env bash
set -eu
apt update && apt install -y build-essential
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

python ./eppo-librarian.py
tail -f /dev/null
