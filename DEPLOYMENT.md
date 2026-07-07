# Agent Office OS Deployment Guide

This guide is for the Hermes deployment operator. Code changes happen in GitHub. Hermes only runs the fixed deployment flow.

## Production Topology

```text
User browser
  -> nginx :80
      /        -> frontend static files
      /api/*   -> office-backend :8000
  -> office-backend
      -> Hermes API bridge :8001
```

Tencent Cloud runs Agent Office OS and Hermes on the same server. The backend reaches Hermes through:

```text
http://host.docker.internal:8001
```

## Release Flow

1. Codex publishes a GitHub Release package named `agent-office-os-<version>.zip`.
2. Silicon Valley mirror downloads the latest GitHub Release and publishes:
   - `/agent-office-os/latest/manifest.json`
   - `/agent-office-os/releases/<version>/agent-office-os-<version>.zip`
3. Tencent watcher checks the mirror every 5 minutes.
4. Tencent watcher verifies SHA256, extracts the package, and runs `ops/deploy.sh`.
5. A deploy report is written to `/opt/agent-office-os-agent/reports/<version>.md`.

## Release Package Requirements

A deployable package must include:

- `docker-compose.yml`
- `nginx.conf`
- `backend/`
- `frontend-dist/` or `dist/`
- `ops/deploy.sh`
- `ops/check.sh`
- `ops/rollback.sh`
- `README.md`
- `docs/`

`ops/deploy.sh` accepts either `frontend-dist/` or `dist/`. If only `dist/` exists, it copies it to `frontend-dist/` before starting nginx.

## Server Directories

Tencent Cloud watcher:

```text
/opt/agent-office-os-agent/
```

Application deploy target:

```text
/opt/agent-office-os/
```

Reports:

```text
/opt/agent-office-os-agent/reports/
```

## Runtime Commands

Check services:

```bash
cd /opt/agent-office-os
docker compose ps
```

View logs:

```bash
cd /opt/agent-office-os
docker compose logs --tail=200 office-backend
docker compose logs --tail=200 nginx
```

Run health checks:

```bash
curl -fsS http://127.0.0.1/api/health
curl -fsS http://127.0.0.1/api/marketplace/agents
```

## Environment

Frontend production config uses same-origin API calls:

```env
VITE_USE_MOCK=false
VITE_API_BASE=
```

Backend production config is set in `docker-compose.yml`:

```yaml
HERMES_URL=http://host.docker.internal:8001
```

## V0.1.0 Acceptance Checks

After deployment, verify:

- The web app opens on port 80.
- `/api/health` returns `status=ok`.
- `/api/marketplace/agents` returns a list or a clear Hermes connection error.
- Organization API is removed: `/api/organization` returns 404.
- Task Center and Outputs Center routes load in the frontend.
- Deployment report says deploy and check succeeded.

## Rollback

The watcher keeps release packages and deployment reports. If a release fails, run the watcher rollback script from the Tencent watcher directory, or redeploy the previous known-good version through the same manifest flow.
