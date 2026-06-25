"""
任务路由
管理 Agent 执行的任务
相当于公司的"任务派发系统"
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OfficeAgent, Task, EventLog
from app.schemas import TaskOut, TaskCreateRequest
from app.adapters.hermes import hermes_adapter

# 创建路由器
router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


def task_to_out(task: Task) -> dict:
    """
    把数据库模型转成响应字典
    小白解释：数据库字段是下划线风格，前端要驼峰风格，这里转换一下
    """
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


@router.get("", response_model=list[TaskOut])
async def list_tasks(db: Session = Depends(get_db)):
    """
    获取所有任务列表
    小白解释：查看办公室里所有任务的执行情况
    """
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return [task_to_out(t) for t in tasks]


@router.post("", response_model=TaskOut)
async def create_task(req: TaskCreateRequest, db: Session = Depends(get_db)):
    """
    创建并派发任务
    小白解释：给某个 Agent 安排一个任务，任务会通过 Hermes 派发出去执行
    """
    # 第一步：检查 Agent 是否存在
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == req.agentId).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    # 第二步：在数据库创建任务记录
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    task = Task(
        id=task_id,
        name=req.title,
        agent_id=req.agentId,
        agent_name=agent.name,
        status="Pending",
        started_at=datetime.utcnow(),
    )
    db.add(task)

    # 第三步：调用 Hermes 派发任务给 Agent 执行
    platform_id = agent.platform_agent_id or req.agentId
    result = await hermes_adapter.execute_task(platform_id, req.title, req.content)

    # 如果 Hermes 返回了任务 ID，更新状态为 Running
    if result.get("task_id"):
        task.status = "Running"
    else:
        # 派发失败，标记为 Failed
        task.status = "Failed"
        task.ended_at = datetime.utcnow()

    # 第四步：更新 Agent 状态为工作中
    agent.status = "WORKING"
    agent.last_active_at = datetime.utcnow()

    # 第五步：写一条事件日志
    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="task",
        title=f"新任务派发：{req.title}",
        description=f"指派给 {agent.name}，状态：{task.status}",
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)

    db.commit()
    db.refresh(task)

    return task_to_out(task)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """
    查询单个任务详情
    小白解释：查看某个任务的详细情况
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="找不到该任务")
    return task_to_out(task)
