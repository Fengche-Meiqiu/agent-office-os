# Hermes Integration Spec

This document defines the V0.1.0 connector contract between Agent Office OS and Hermes. Hermes is the first connector. Future platforms must implement the same normalized model inside Agent Office OS.

## Connector Principles

- Agent Office OS owns the user experience, routing, task center, outputs center, and meeting room.
- Hermes owns its native agent runtime and task execution.
- The connector must normalize external platform data into stable Office OS fields.
- Missing required fields must be visible as data quality issues instead of silently hidden.

## Required Agent Fields

Every synced agent must provide or map to these fields:

| Field | Required | Description |
| --- | --- | --- |
| `external_id` | yes | Stable Hermes agent id. |
| `source_platform` | yes | `hermes` for this connector. |
| `name` | yes | Human-readable agent name. |
| `role` | yes | Job-like role, for example research analyst or product manager. |
| `summary` | yes | Short profile shown in marketplace cards. |
| `description` | yes | Full introduction shown on details pages. |
| `capabilities` | yes | List of concrete abilities. |
| `tags` | no | Search and grouping labels. |
| `avatar_url` | no | Optional avatar. |
| `status` | yes | `available`, `busy`, `offline`, or `unknown`. |
| `metadata` | no | Raw platform-specific details. |

If Hermes cannot provide a required field, the connector should mark the field as missing and surface a clear "needs Hermes completion" state in the UI.

## Minimum Hermes APIs

Agent sync:

```http
GET /agents
```

Expected normalized response:

```json
{
  "agents": [
    {
      "external_id": "hermes-agent-id",
      "name": "Nuwa",
      "role": "Meeting summarizer",
      "summary": "Creates meeting notes and action items.",
      "description": "Full agent introduction.",
      "capabilities": ["summarize meetings", "extract action items"],
      "tags": ["meeting", "summary"],
      "status": "available",
      "metadata": {}
    }
  ]
}
```

Chat message:

```http
POST /agents/{external_id}/chat
```

Task message:

```http
POST /agents/{external_id}/task
```

Expected request:

```json
{
  "conversation_id": "office-conversation-id",
  "message": "user message or task instruction",
  "attachments": []
}
```

Expected response:

```json
{
  "message_id": "hermes-message-id",
  "content": "agent response",
  "task_id": "optional-hermes-task-id",
  "status": "completed",
  "attachments": []
}
```

## V0.1.0 Acceptance Mapping

- Marketplace sync must use Hermes as the source of truth when `VITE_USE_MOCK=false` and backend Hermes URL is configured.
- `/chat` should create normal conversation messages.
- `/task` should create a task record, forward the task to Hermes, and show Hermes response in chat and Task Center.
- Task outputs and meeting outputs must appear in Outputs Center.

## Future Connector Requirements

Any new platform connector must implement:

- Agent list sync.
- Agent detail normalization.
- Chat send/receive.
- Task send/receive.
- Attachment metadata mapping.
- Error and timeout handling.
- Data quality reporting for missing fields.