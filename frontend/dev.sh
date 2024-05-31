#!/usr/bin/env bash

env | grep -E '^(FRONTEND_PORT|BACKEND_PORT)' >.env

yarn install
yarn dev -p "${FRONTEND_PORT}"
