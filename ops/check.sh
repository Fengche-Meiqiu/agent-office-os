#!/usr/bin/env bash
set -euo pipefail

APP_BASE_URL="${APP_BASE_URL:-http://127.0.0.1}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
HERMES_URL="${HERMES_URL:-http://127.0.0.1:8001}"

check_url() {
  local name="$1"
  local url="$2"
  echo "[check] ${name}: ${url}"
  curl -fsS -m 20 "${url}" >/tmp/agent-office-check.out
  head -c 500 /tmp/agent-office-check.out || true
  echo
}

check_url "frontend/root" "${APP_BASE_URL}/"
check_url "backend/health" "${BACKEND_URL}/api/health"

if curl -fsS -m 20 "${HERMES_URL}/api/health" >/tmp/hermes-health.out; then
  echo "[check] hermes/health: OK"
  head -c 500 /tmp/hermes-health.out || true
  echo
else
  echo "[check] hermes/health: WARN, Hermes health endpoint not reachable"
fi

echo "[check] OK"
