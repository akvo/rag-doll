#!/usr/bin/env bash
#shellcheck disable=SC2016

set -eu

docker-compose exec -T db bash -c 'pg_dump --user idc --clean --create --format plain idh_idc > /docker-entrypoint-initdb.d/001-init.sql; echo "Export done"'
