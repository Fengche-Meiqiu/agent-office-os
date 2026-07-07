#!/usr/bin/env bash
set -euo pipefail

MANIFEST_URL="${MANIFEST_URL:-http://47.77.194.50/agent-office-os/latest/manifest.json}"
AGENT_HOME="${AGENT_HOME:-/opt/agent-office-os-agent}"
CURRENT_VERSION_FILE="${AGENT_HOME}/.deployed-version"
LOCK_FILE="${AGENT_HOME}/.deploy.lock"

mkdir -p "${AGENT_HOME}/downloads" "${AGENT_HOME}/releases" "${AGENT_HOME}/reports" "${AGENT_HOME}/logs"

if [ -f "${LOCK_FILE}" ]; then
  echo "[watcher] lock exists, another deployment may be running: ${LOCK_FILE}"
  exit 0
fi

touch "${LOCK_FILE}"
cleanup() {
  rm -f "${LOCK_FILE}"
}
trap cleanup EXIT

MANIFEST_FILE="${AGENT_HOME}/latest-manifest.json"
curl -fsSL "${MANIFEST_URL}" -o "${MANIFEST_FILE}"

read_manifest() {
  python3 - "$MANIFEST_FILE" "$1" "$2" <<'PY'
import json
import sys
path, key, default = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
print(data.get(key, default))
PY
}

VERSION="$(read_manifest version '')"
PACKAGE_URL="$(read_manifest packageUrl '')"
EXPECTED_SHA="$(read_manifest sha256 '')"
DEPLOY_SCRIPT="$(read_manifest deployScript 'ops/deploy.sh')"
CHECK_SCRIPT="$(read_manifest checkScript 'ops/check.sh')"
ROLLBACK_SCRIPT="$(read_manifest rollbackScript 'ops/rollback.sh')"

if [ -z "${VERSION}" ] || [ -z "${PACKAGE_URL}" ] || [ -z "${EXPECTED_SHA}" ]; then
  echo "[watcher] invalid manifest: version, packageUrl, and sha256 are required"
  exit 1
fi

CURRENT_VERSION=""
if [ -f "${CURRENT_VERSION_FILE}" ]; then
  CURRENT_VERSION="$(cat "${CURRENT_VERSION_FILE}")"
fi

if [ "${VERSION}" = "${CURRENT_VERSION}" ]; then
  echo "[watcher] already deployed ${VERSION}"
  exit 0
fi

echo "[watcher] new version detected: ${VERSION}"

PKG="${AGENT_HOME}/downloads/agent-office-os-${VERSION}.zip"
RELEASE_DIR="${AGENT_HOME}/releases/${VERSION}"
REPORT="${AGENT_HOME}/reports/${VERSION}.md"

rm -rf "${RELEASE_DIR}"
mkdir -p "${RELEASE_DIR}"

curl -fL "${PACKAGE_URL}" -o "${PKG}"
ACTUAL_SHA="$(sha256sum "${PKG}" | awk '{print $1}')"

if [ "${ACTUAL_SHA}" != "${EXPECTED_SHA}" ]; then
  echo "[watcher] sha256 mismatch"
  echo "expected=${EXPECTED_SHA}"
  echo "actual=${ACTUAL_SHA}"
  exit 1
fi

unzip -q "${PKG}" -d "${RELEASE_DIR}"

{
  echo "# Agent Office OS Deployment Report"
  echo
  echo "- Version: ${VERSION}"
  echo "- Time UTC: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Package URL: ${PACKAGE_URL}"
  echo "- SHA256: ${ACTUAL_SHA}"
  echo
  echo "## Deploy"
} > "${REPORT}"

cd "${RELEASE_DIR}"

if bash "${DEPLOY_SCRIPT}" >> "${REPORT}" 2>&1; then
  echo >> "${REPORT}"
  echo "## Check" >> "${REPORT}"
  if bash "${CHECK_SCRIPT}" >> "${REPORT}" 2>&1; then
    echo "${VERSION}" > "${CURRENT_VERSION_FILE}"
    echo >> "${REPORT}"
    echo "## Result" >> "${REPORT}"
    echo "SUCCESS" >> "${REPORT}"
    echo "[watcher] deployed ${VERSION} successfully"
    exit 0
  fi
fi

echo >> "${REPORT}"
echo "## Result" >> "${REPORT}"
echo "FAILED" >> "${REPORT}"

if [ -f "${ROLLBACK_SCRIPT}" ]; then
  echo >> "${REPORT}"
  echo "## Rollback" >> "${REPORT}"
  bash "${ROLLBACK_SCRIPT}" >> "${REPORT}" 2>&1 || true
fi

echo "[watcher] deployment failed, see ${REPORT}"
exit 1
