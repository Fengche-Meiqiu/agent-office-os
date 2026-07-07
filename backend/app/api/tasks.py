import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.hermes import hermes_adapter
from app.database import get_db
from app.models import EventLog, OfficeAgent, Output, Task
from app.schemas import TaskCreateRequest, TaskOut

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


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


def _status_from_hermes(result: dict) -> str:
    status = str(result.get("status") or "").lower()
    if status in {"completed", "done", "success", "succeeded"}:
        return "Completed"
    if status in {"failed", "error"} or result.get("error"):
        return "Failed"
    if result.get("task_id") or result.get("id"):
        return "Running"
    if _task_result_text(result):
        return "Completed"
    return "Failed"


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
    task.status = _status_from_hermes(result)

    output_text = _task_result_text(result)
    if task.status in {"Completed", "Failed"}:
        task.ended_at = datetime.utcnow()
        task.duration = max(0, int((task.ended_at - task.started_at).total_seconds() // 60)) if task.started_at else 0

    if output_text:
        output = Output(
            id=f"output_{uuid.uuid4().hex[:8]}",
            name=f"{title}.md",
            type="markdown",
            source="task",
            content=output_text,
            created_at=datetime.utcnow(),
        )
        db.add(output)
        db.flush()
        task.output_id = output.id

    perf = agent.performance or {}
    perf["totalTasks"] = int(perf.get("totalTasks", 0)) + 1
    if task.status == "Completed":
        perf["successTasks"] = int(perf.get("successTasks", 0)) + 1
    elif task.status == "Failed":
        perf["failedTasks"] = int(perf.get("failedTasks", 0)) + 1
    agent.performance = perf
    agent.status = "WORKING" if task.status == "Running" else "ONLINE"
    agent.last_active_at = datetime.utcnow()

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
    return task_to_out(task)
