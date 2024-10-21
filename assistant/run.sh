#!/usr/bin/env bash
set -eu
apt update && apt install -y build-essential
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

pip -q install --cache-dir=.pip -e /lib/Akvo_rabbitmq_client

python -m seeder.generate_prompt_sqlite
python ./assistant.py
