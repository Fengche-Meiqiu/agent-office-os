import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.tasks import apply_hermes_task_result
from app.database import get_db
from app.models import EventLog, OfficeAgent, Task
from app.schemas import WebhookPayload

router = APIRouter(prefix="/api/webhook", tags=["webhook"])


def _find_task(db: Session, task_id: str | None) -> Task | None:
    if not task_id:
        return None
    return db.query(Task).filter((Task.id == task_id) | (Task.platform_task_id == task_id)).first()


@router.post("/hermes")
async def hermes_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    event = payload.event
    title = ""
    description = ""

    if event in ("task_created", "task_started", "task_completed", "task_failed"):
        task = _find_task(db, payload.task_id)
        if task:
            status_map = {
                "task_created": "running",
                "task_started": "running",
                "task_completed": "completed",
                "task_failed": "failed",
            }
            hermes_result = {
                "task_id": payload.task_id,
                "status": payload.status or status_map.get(event),
                "result": payload.result,
            }
            apply_hermes_task_result(db, task, hermes_result)
            title = f"Task webhook: {task.name}"
            description = f"Task ID: {task.id}; Hermes ID: {payload.task_id}; status: {task.status}"
        else:
            title = f"Task webhook: {event}"
            description = f"Hermes task ID not found locally: {payload.task_id}"

    elif event in ("agent_online", "agent_offline"):
        agent = None
        if payload.agent_id:
            agent = db.query(OfficeAgent).filter(OfficeAgent.platform_agent_id == payload.agent_id).first()

        if agent:
            agent.status = "ONLINE" if event == "agent_online" else "OFFLINE"
            title = f"Agent webhook: {agent.name}"
            description = f"Platform agent ID: {payload.agent_id}; event: {event}"
        else:
            title = f"Agent webhook: {event}"
            description = f"Platform agent ID not found locally: {payload.agent_id}"

    else:
        title = f"Unknown webhook: {event}"
        description = f"payload: {payload.model_dump()}"

    db.add(EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="task" if event.startswith("task_") else "agent",
        title=title,
        description=description,
        timestamp=datetime.utcnow(),
    ))
    db.commit()
    return {"message": "webhook processed", "event": event}