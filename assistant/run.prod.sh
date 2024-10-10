#!/usr/bin/env bash
set -eu

python -m seeder.generate_prompt_sqlite
python ./assistant.py
