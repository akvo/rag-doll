#!/usr/bin/env bash

env | grep -E '^(FRONTEND_PORT|BACKEND_PORT)' > .env
env | grep -E '^(NEXT_PUBLIC_VAPID_PUBLIC_KEY)' >> .env
env | grep -E '^(NEXT_PUBLIC_VAPID_PRIVATE_KEY)' >> .env


yarn install
yarn dev -p "${FRONTEND_PORT}"
