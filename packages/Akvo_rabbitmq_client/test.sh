#!/usr/bin/env bash
set -eu

set -eu
pip -q install --upgrade pip
pip -q install --cache-dir=.pip -e /app/Akvo_rabbitmq_client

python -m unittest discover -s ./Akvo_rabbitmq_client/tests
