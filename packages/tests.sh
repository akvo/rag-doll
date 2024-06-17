#!/usr/bin/env bash
set -eu

./Akvo_rabbitmq_client/test.sh

tail -f /dev/null
