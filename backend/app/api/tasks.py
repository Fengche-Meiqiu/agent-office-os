import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.hermes import hermes_adapter
from app.database import get_db
from app.models import EventLog, OfficeAgent, Output, Task
from app.schemas import TaskCreateRequest, TaskOut

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

TERMINAL_STATUSES = {"Completed", "Failed"}


def task_to_out(task: Task) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "agentId": task.agent_id,
        "agentName": task.agent_name,
        "status": task.status,
        "startedAt": task.started_at.isoformat() if task.started_at else None,
        "endedAt": task.ended_at.isoformat() if task.ended_at else None,
        "duration": task.duration,
        "outputId": task.output_id,
    }


def _task_result_text(result: dict) -> str:
    value = result.get("result") or result.get("content") or result.get("reply") or result.get("message") or result.get("output")
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _external_task_id(result: dict) -> str:
    value = result.get("task_id") or result.get("taskId") or result.get("id")
    return str(value) if value else ""


def _status_from_hermes(result: dict) -> str:
    status = str(result.get("status") or "").lower()
    if status in {"completed", "complete", "done", "success", "succeeded"}:
        return "Completed"
    if status in {"failed", "error", "cancelled", "canceled"} or result.get("error"):
        return "Failed"
    if _external_task_id(result):
        return "Running"
    if _task_result_text(result):
        return "Completed"
    return "Failed"


def _finish_task_if_needed(task: Task, status: str):
    if status not in TERMINAL_STATUSES or task.ended_at:
        return
    task.ended_at = datetime.utcnow()
    task.duration = max(0, int((task.ended_at - task.started_at).total_seconds() // 60)) if task.started_at else 0


def _attach_output_if_present(db: Session, task: Task, result: dict):
    output_text = _task_result_text(result)
    if not output_text or task.output_id:
        return
    output = Output(
        id=f"output_{uuid.uuid4().hex[:8]}",
        name=f"{task.name}.md",
        type="markdown",
        source="task",
        content=output_text,
        created_at=datetime.utcnow(),
    )
    db.add(output)
    db.flush()
    task.output_id = output.id


def _update_agent_after_task(agent: OfficeAgent, task: Task, previous_status: str):
    perf = agent.performance or {}
    if previous_status != task.status:
        if task.status == "Completed":
            perf["successTasks"] = int(perf.get("successTasks", 0)) + 1
        elif task.status == "Failed":
            perf["failedTasks"] = int(perf.get("failedTasks", 0)) + 1
    agent.performance = perf
    agent.status = "WORKING" if task.status == "Running" else "ONLINE"
    agent.last_active_at = datetime.utcnow()


def apply_hermes_task_result(db: Session, task: Task, result: dict) -> Task:
    previous_status = task.status
    external_id = _external_task_id(result)
    if external_id and not task.platform_task_id:
        task.platform_task_id = external_id

    task.status = _status_from_hermes(result)
    _finish_task_if_needed(task, task.status)
    _attach_output_if_present(db, task, result)

    agent = db.query(OfficeAgent).filter(OfficeAgent.id == task.agent_id).first()
    if agent:
        _update_agent_after_task(agent, task, previous_status)
    return task


async def sync_task_from_hermes(db: Session, task: Task) -> Task:
    if task.status in TERMINAL_STATUSES or not task.platform_task_id:
        return task

    result = await hermes_adapter.get_task(task.platform_task_id)
    if result.get("status") == "unknown" and result.get("error"):
        return task

    apply_hermes_task_result(db, task, result)
    db.add(EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="task",
        title=f"Task synced: {task.name}",
        description=f"Agent: {task.agent_name}; status: {task.status}",
        timestamp=datetime.utcnow(),
    ))
    return task


async def create_and_dispatch_task(db: Session, agent: OfficeAgent, title: str, content: str) -> Task:
    now = datetime.utcnow()
    task = Task(
        id=f"task_{uuid.uuid4().hex[:8]}",
        name=title,
        agent_id=agent.id,
        agent_name=agent.name,
        status="Pending",
        started_at=now,
    )
    db.add(task)
    db.flush()

    platform_id = agent.platform_agent_id or agent.id
    result = await hermes_adapter.execute_task(platform_id, title, content)
    apply_hermes_task_result(db, task, result)

    perf = agent.performance or {}
    perf["totalTasks"] = int(perf.get("totalTasks", 0)) + 1
    agent.performance = perf

    db.add(EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="task",
        title=f"Task dispatched: {title}",
        description=f"Agent: {agent.name}; status: {task.status}",
        timestamp=datetime.utcnow(),
    ))
    return task


@router.get("", response_model=list[TaskOut])
async def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    for task in tasks:
        await sync_task_from_hermes(db, task)
    db.commit()
    return [task_to_out(task) for task in tasks]


@router.post("", response_model=TaskOut)
async def create_task(req: TaskCreateRequest, db: Session = Depends(get_db)):
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == req.agentId).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    task = await create_and_dispatch_task(db, agent, req.title, req.content)
    db.commit()
    db.refresh(task)
    return task_to_out(task)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await sync_task_from_hermes(db, task)
    db.commit()
    db.refresh(task)
    return task_to_out(task)