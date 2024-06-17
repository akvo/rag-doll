#!/usr/bin/env bash
#shellcheck disable=SC2039
#shellcheck disable=SC3040

set -exuo pipefail

IMAGE_PREFIX="eu.gcr.io/akvo-lumen/agriconnect"
CI_COMMIT=$(git rev-parse --short "$GITHUB_SHA")

echo "CI_COMMIT=${CI_COMMIT}"

dc() {
    docker compose \
        --ansi never \
        -f docker-compose.yml \
        -f docker-compose.test.yml \
        "$@"
}

backend_build() {

    cp ./setup.cfg ./backend/setup.cfg
    docker build \
        --tag "${IMAGE_PREFIX}/backend:latest" \
        --tag "${IMAGE_PREFIX}/backend:${CI_COMMIT}" backend
}

cp .env.template .env

backend_build
docker compose \
    -f docker-compose.yml \
    -f docker-compose.test \
    run -T backend ./test.sh
