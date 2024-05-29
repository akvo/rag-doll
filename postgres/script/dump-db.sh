#!/usr/bin/env bash
#shellcheck disable=SC2016

set -eu

docker compose exec -T postgres bash -c 'pg_dump --user akvo --clean --create --format plain dev > /docker-entrypoint-initdb.d/001-init.sql; echo "Export done"'
