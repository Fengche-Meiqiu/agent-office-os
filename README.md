# Agent Office OS

Agent Office OS is a Hermes-backed workspace for selecting AI agents, chatting with them, starting tasks, running basic meetings, and collecting results.

## V0.1.0 Goal

V0.1.0 focuses on one reliable user journey:

Open the system -> sync agents from Hermes -> review agent details -> hire an agent -> chat -> send a `/task` request -> monitor it in Task Center -> review the result in Outputs.

## Scope

Included in V0.1.0:

- Hermes agent synchronization as the first platform connector.
- Agent marketplace and office agent list.
- Single-agent `/chat` and `/task` flows.
- Task Center for task status tracking.
- Outputs Center for task and meeting results.
- Basic meeting room flow.
- Production deployment through GitHub Release, Silicon Valley mirror, and Tencent watcher.
- Organization structure removed from product navigation and backend API.

Deferred after V0.1.0:

- Full meeting pause/resume and continuous autonomous discussion.
- Mature file transfer in both directions.
- Multiple external agent platforms.
- Advanced role-based permissions.

## Local Development

Install frontend dependencies:

```bash
npm ci
```

Run the frontend:

```bash
npm run dev
```

Run the backend locally:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Quality Gates

Before a release package is published, run:

```bash
npm run check
npm run build
python -m compileall backend/app
python -m pytest backend/tests
```

## Deployment Channel

V0.1.0 is deployed by release package:

1. Codex prepares and publishes a GitHub Release package.
2. Silicon Valley mirror pulls the GitHub Release and exposes `manifest.json` plus the package.
3. Tencent watcher checks the mirror every 5 minutes.
4. Tencent watcher downloads, verifies SHA256, extracts, and runs `ops/deploy.sh`.
5. Deployment reports are written under `/opt/agent-office-os-agent/reports/`.

Hermes executes deployment commands only. Code changes are made in this repository.

## Connector Standard

Hermes is the first implementation of the platform connector contract. See `docs/HERMES_INTEGRATION_SPEC.md` for required fields and API expectations.
