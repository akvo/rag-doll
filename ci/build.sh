#!/usr/bin/env bash
#shellcheck disable=SC2039
#shellcheck disable=SC3040

set -exuo pipefail

IMAGE_PREFIX="eu.gcr.io/akvo-lumen/agriconnect"
CI_COMMIT=$(git rev-parse --short "$GITHUB_SHA")

echo "CI_COMMIT=${CI_COMMIT}"

backend_build() {

    cp ./setup.cfg ./backend/setup.cfg
    docker build \
        --tag "${IMAGE_PREFIX}/backend:latest" \
        --tag "${IMAGE_PREFIX}/backend:${CI_COMMIT}" backend
}

package_build() {
    cd "$(pwd)/packages/Akvo_rabbitmq_client"
    python setup.py sdist bdist_wheel
    cd "$(git rev-parse --show-toplevel)"
}

cp env.template .env

backend_build
package_build
docker compose \
    -f docker-compose.test.yml \
    run -T backend ./test.sh
