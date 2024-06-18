#!/usr/bin/env bash

set -euo pipefail

pip -q install --upgrade pip
pip -q install --cache-dir=.pip -r requirements.txt

pip install --cache-dir=.pip Akvo_rabbitmq_client --no-index --find-links file:/app/Akvo_rabbitmq_client

echo "Running tests"
COVERAGE_PROCESS_START=./.coveragerc \
  coverage run --parallel-mode --concurrency=thread,gevent --rcfile=./.coveragerc \
  /usr/local/bin/pytest -vvv -rP

echo "Coverage"
coverage combine --rcfile=./.coveragerc
coverage report -m --rcfile=./.coveragerc

if [[ -n "${COVERALLS_REPO_TOKEN:-}" ]] ; then
  coveralls
fi

flake8
