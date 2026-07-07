#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/agent-office-os}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

if [ ! -f "${COMPOSE_FILE}" ]; then
  echo "[deploy] ${COMPOSE_FILE} not found in release package"
  echo "[deploy] Connectivity or documentation-only package; no deployment changes applied."
  exit 0
fi

mkdir -p "${APP_DIR}"

rsync -a --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'dist' \
  ./ "${APP_DIR}/"

cd "${APP_DIR}"

if docker compose version >/dev/null 2>&1; then
  docker compose -f "${COMPOSE_FILE}" up -d --build
else
  docker-compose -f "${COMPOSE_FILE}" up -d --build
fi

echo "[deploy] deployed to ${APP_DIR}"
