#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-Fengche-Meiqiu/agent-office-os}"
GITHUB_API="${GITHUB_API:-https://api.github.com/repos/${REPO}/releases/latest}"
MIRROR_ROOT="${MIRROR_ROOT:-/var/www/agent-office-os}"
WORK_ROOT="${WORK_ROOT:-/opt/agent-office-mirror/work}"

mkdir -p "${MIRROR_ROOT}/latest" "${MIRROR_ROOT}/releases" "${WORK_ROOT}"

LATEST_JSON="${WORK_ROOT}/latest-release.json"
curl -fsSL "${GITHUB_API}" -o "${LATEST_JSON}"

VERSION="$(python3 - "$LATEST_JSON" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)
print(data.get('tag_name') or data.get('name') or '')
PY
)"

if [ -z "${VERSION}" ]; then
  echo "[mirror] release version not found"
  exit 1
fi

ASSET_URL="$(python3 - "$LATEST_JSON" <<'PY'
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    data = json.load(f)
for asset in data.get('assets', []):
    name = asset.get('name', '')
    if name.endswith('.zip') and 'agent-office-os' in name:
        print(asset.get('browser_download_url', ''))
        break
PY
)"

if [ -z "${ASSET_URL}" ]; then
  echo "[mirror] no agent-office-os zip asset found for ${VERSION}"
  exit 1
fi

PKG_NAME="$(basename "${ASSET_URL%%\?*}")"
VERSION_DIR="${MIRROR_ROOT}/releases/${VERSION}"
PKG_PATH="${VERSION_DIR}/${PKG_NAME}"
mkdir -p "${VERSION_DIR}"

if [ ! -f "${PKG_PATH}" ]; then
  echo "[mirror] downloading ${ASSET_URL}"
  curl -fL "${ASSET_URL}" -o "${PKG_PATH}.tmp"
  mv "${PKG_PATH}.tmp" "${PKG_PATH}"
fi

SHA256="$(sha256sum "${PKG_PATH}" | awk '{print $1}')"

cat > "${MIRROR_ROOT}/latest/manifest.json" <<EOF
{
  "version": "${VERSION}",
  "packageUrl": "http://47.77.194.50/agent-office-os/releases/${VERSION}/${PKG_NAME}",
  "sha256": "${SHA256}",
  "deployScript": "ops/deploy.sh",
  "checkScript": "ops/check.sh",
  "rollbackScript": "ops/rollback.sh",
  "createdAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

echo "[mirror] mirrored ${VERSION}"
echo "[mirror] package=${PKG_PATH}"
echo "[mirror] sha256=${SHA256}"
