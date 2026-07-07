# Silicon Valley Release Mirror Setup

This server caches GitHub release packages so Tencent Cloud Hermes does not need to access GitHub directly.

## Server

```text
IP: 47.77.194.50
Role: release mirror
Static root: /var/www/agent-office-os
Mirror worker: /opt/agent-office-mirror
```

## Public URLs

```text
http://47.77.194.50/agent-office-os/latest/manifest.json
http://47.77.194.50/agent-office-os/releases/<version>/<package>.zip
```

## Install

```bash
apt update
apt install -y nginx curl unzip tar python3
systemctl enable nginx
systemctl start nginx

mkdir -p /var/www/agent-office-os/latest
mkdir -p /var/www/agent-office-os/releases
mkdir -p /opt/agent-office-mirror/logs
```

Copy `ops/mirror-sync.sh` to:

```text
/opt/agent-office-mirror/mirror-sync.sh
```

Make it executable:

```bash
chmod +x /opt/agent-office-mirror/mirror-sync.sh
```

## Run Manually

```bash
REPO=Fengche-Meiqiu/agent-office-os /opt/agent-office-mirror/mirror-sync.sh
curl http://127.0.0.1/agent-office-os/latest/manifest.json
```

## Cron

Run every 5 minutes:

```bash
(crontab -l 2>/dev/null; echo '*/5 * * * * REPO=Fengche-Meiqiu/agent-office-os /opt/agent-office-mirror/mirror-sync.sh >> /opt/agent-office-mirror/logs/mirror.log 2>&1') | crontab -
crontab -l
```

## Notes

- This script mirrors the latest GitHub Release zip asset whose name contains `agent-office-os` and ends with `.zip`.
- It generates `latest/manifest.json` with a mirror-local `packageUrl`.
- It does not deploy anything. It only hosts packages.
