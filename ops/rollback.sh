#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/agent-office-os}"
BACKUP_DIR="${BACKUP_DIR:-/opt/agent-office-os-backups/latest}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

if [ ! -d "${BACKUP_DIR}" ]; then
  echo "[rollback] no backup directory found: ${BACKUP_DIR}"
  echo "[rollback] nothing changed"
  exit 0
fi

mkdir -p "${APP_DIR}"
rsync -a --delete "${BACKUP_DIR}/" "${APP_DIR}/"

cd "${APP_DIR}"
if [ -f "${COMPOSE_FILE}" ]; then
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" up -d --build
  else
    docker-compose -f "${COMPOSE_FILE}" up -d --build
  fi
fi

echo "[rollback] restored ${APP_DIR} from ${BACKUP_DIR}"
