#!/usr/bin/env bash
#shellcheck disable=SC2039

set -euo pipefail

psql --user idc --no-align --list | \
    awk -F'|' '/^test/ {print $1}' | \
    while read -r dbname
    do
	psql --user idc --dbname idh_idc -c "DROP DATABASE ${dbname}"
    done

echo "Done"
