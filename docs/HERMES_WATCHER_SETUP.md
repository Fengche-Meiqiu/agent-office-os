# Hermes Release Watcher Setup

Tencent Cloud Hermes uses this watcher to poll the Silicon Valley mirror and deploy only when the release version changes.

## Server

```text
IP: 82.157.75.207
SSH user: ubuntu
Hermes app: ~/.hermes/hermes-agent/
Hermes gateway: systemd hermes-gateway
Hermes API bridge: systemd hermes-api, port 8001
Watcher home: /opt/agent-office-os-agent
Manifest URL: http://47.77.194.50/agent-office-os/latest/manifest.json
```

## Install

```bash
sudo mkdir -p /opt/agent-office-os-agent/downloads
sudo mkdir -p /opt/agent-office-os-agent/releases
sudo mkdir -p /opt/agent-office-os-agent/reports
sudo mkdir -p /opt/agent-office-os-agent/logs
sudo chown -R "$USER":"$USER" /opt/agent-office-os-agent
```

Copy `ops/check-release.sh` to:

```text
/opt/agent-office-os-agent/check-release.sh
```

Make it executable:

```bash
chmod +x /opt/agent-office-os-agent/check-release.sh
```

## Run Manually

```bash
MANIFEST_URL=http://47.77.194.50/agent-office-os/latest/manifest.json \
AGENT_HOME=/opt/agent-office-os-agent \
/opt/agent-office-os-agent/check-release.sh
```

Check report:

```bash
cat /opt/agent-office-os-agent/.deployed-version
ls -la /opt/agent-office-os-agent/reports
```

## Cron

Run every 5 minutes:

```bash
(crontab -l 2>/dev/null; echo '*/5 * * * * MANIFEST_URL=http://47.77.194.50/agent-office-os/latest/manifest.json AGENT_HOME=/opt/agent-office-os-agent /opt/agent-office-os-agent/check-release.sh >> /opt/agent-office-os-agent/logs/watcher.log 2>&1') | crontab -
crontab -l
```

## Report Files

```text
/opt/agent-office-os-agent/.deployed-version
/opt/agent-office-os-agent/latest-manifest.json
/opt/agent-office-os-agent/reports/<version>.md
/opt/agent-office-os-agent/logs/watcher.log
```

## Rules

- Hermes must not edit application source code on the server.
- Hermes only runs scripts included in the release package: `ops/deploy.sh`, `ops/check.sh`, and `ops/rollback.sh`.
- Every deployment must write a report.
- A release is considered deployed only after `ops/check.sh` succeeds.
