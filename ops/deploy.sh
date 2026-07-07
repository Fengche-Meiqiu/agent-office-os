#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/agent-office-os}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

if [ ! -f "${COMPOSE_FILE}" ]; then
  echo "[deploy] ${COMPOSE_FILE} not found in release package"
  echo "[deploy] Connectivity or documentation-only package; no deployment changes applied."
  exit 0
fi

if [ ! -d frontend-dist ] && [ -d dist ]; then
  rm -rf frontend-dist
  cp -a dist frontend-dist
fi

if [ ! -d frontend-dist ]; then
  echo "[deploy] frontend-dist not found. Build the frontend before packaging the release."
  exit 1
fi

mkdir -p "${APP_DIR}"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude 'dist' \
    ./ "${APP_DIR}/"
else
  echo "[deploy] rsync not found; using tar copy fallback"
  tmp_tar="$(mktemp)"
  tar --exclude='.git' --exclude='node_modules' --exclude='dist' -cf "${tmp_tar}" .
  rm -rf "${APP_DIR:?}"/*
  tar -xf "${tmp_tar}" -C "${APP_DIR}"
  rm -f "${tmp_tar}"
fi

cd "${APP_DIR}"

if docker compose version >/dev/null 2>&1; then
  docker compose -f "${COMPOSE_FILE}" up -d --build
else
  docker-compose -f "${COMPOSE_FILE}" up -d --build
fi

echo "[deploy] deployed to ${APP_DIR}"