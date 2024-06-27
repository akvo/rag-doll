#!/usr/bin/env bash

set -euo pipefail

pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

pip -q install --cache-dir=.pip /lib/Akvo_rabbitmq_client

# Read backend port from environment variable
BACKEND_PORT=${BACKEND_PORT}

# Start the FastAPI server in the background and capture the process ID
uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
FASTAPI_PID=$!

# Give the server some time to start
sleep 5

echo "Running tests"
COVERAGE_PROCESS_START=./.coveragerc \
  coverage run --parallel-mode --concurrency=thread,gevent --rcfile=./.coveragerc \
  /usr/local/bin/pytest -vvv -rP

# Shut down the FastAPI server
kill $FASTAPI_PID

echo "Coverage"
coverage combine --rcfile=./.coveragerc
coverage report -m --rcfile=./.coveragerc

if [[ -n "${COVERALLS_REPO_TOKEN:-}" ]] ; then
  coveralls
fi

flake8
