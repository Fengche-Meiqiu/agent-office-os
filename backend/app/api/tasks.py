"""
任务路由（V2 重写）
核心变更：
1. 使用 get_adapter_or_raise(agent.platform) 路由，不硬编码 hermes_adapter
2. 调用 resolve_platform_id 统一身份映射
3. task_to_out 返回 result/progress/currentStep/skillIds
4. create_task 支持传入 skillIds，调用 execute_task 时传 skills
5. 新增 GET /{task_id}/logs 查询任务执行日志
6. 任务创建后 SSE 推送 task_status
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OfficeAgent, Task, TaskLog, AgentMapping, EventLog
from app.schemas import TaskOut, TaskCreateRequest, TaskLogOut
from app.adapters import get_adapter_or_raise
from app.adapters.base import AdapterError
from app.api.sse import broadcast

# 创建路由器
router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


def resolve_platform_id(agent: OfficeAgent, db: Session) -> str:
    """统一身份映射：查 AgentMapping 表获取真实 platform_agent_id"""
    mapping = db.query(AgentMapping).filter(
        AgentMapping.office_agent_id == agent.id
    ).first()
    if mapping and mapping.platform_agent_id:
        return mapping.platform_agent_id
    if agent.platform_agent_id:
        return agent.platform_agent_id
    return agent.id


def task_to_out(task: Task) -> dict:
    """数据库模型 → 响应字典（V2 扩展 result/progress/currentStep/skillIds/platformTaskId）"""
    return {
        "id": task.id,
        "name": task.name,
        "agentId": task.agent_id,
        "agentName": task.agent_name or "",
        "status": task.status,
        "startedAt": task.started_at.isoformat() if task.started_at else None,
        "endedAt": task.ended_at.isoformat() if task.ended_at else None,
        "duration": task.duration,
        "outputId": task.output_id,
        # V2 新增字段
        "result": task.result,
        "progress": task.progress or 0,
        "currentStep": task.current_step,
        "skillIds": task.skill_ids or [],
        "platformTaskId": task.platform_task_id,  # 源平台任务 ID
    }


def task_log_to_out(log: TaskLog) -> dict:
    """TaskLog 模型 → 响应字典"""
    return {
        "id": log.id,
        "taskId": log.task_id,
        "step": log.step or "",
        "detail": log.detail or "",
        "level": log.level or "info",
        "timestamp": log.timestamp.isoformat() if log.timestamp else "",
    }


@router.get("", response_model=list[TaskOut])
async def list_tasks(db: Session = Depends(get_db)):
    """获取所有任务列表"""
    tasks = db.query(Task).order_by(Task.created_at.desc()).all()
    return [task_to_out(t) for t in tasks]


@router.post("", response_model=TaskOut)
async def create_task(req: TaskCreateRequest, db: Session = Depends(get_db)):
    """
    创建并派发任务
    小白解释：给某个 Agent 安排任务，通过 Adapter 派发给源平台执行
    V2：支持传入 skillIds，execute_task 时传 skills 参数
    """
    import traceback
    try:
        # 第一步：检查 Agent 是否存在
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == req.agentId).first()
        if not agent:
            raise HTTPException(status_code=404, detail="找不到该 Agent")

        # 第二步：创建任务记录
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            name=req.title,
            agent_id=req.agentId,
            agent_name=agent.name,
            status="Pending",
            started_at=datetime.utcnow(),
            skill_ids=req.skillIds or [],
        )
        db.add(task)

        # 第三步：调用 Adapter 派发任务
        platform_id = resolve_platform_id(agent, db)
        try:
            adapter = get_adapter_or_raise(agent.platform)
        except ValueError as e:
            task.status = "Failed"
            task.ended_at = datetime.utcnow()
            db.commit()
            raise HTTPException(status_code=502, detail=str(e))
        try:
            result = await adapter.execute_task(
                platform_id, req.title, req.content, skills=req.skillIds or []
            )
        except AdapterError as e:
            task.status = "Failed"
            task.ended_at = datetime.utcnow()
            task.result = f"派发失败：{e.detail}"
            db.commit()
            raise HTTPException(
                status_code=502,
                detail=f"任务派发失败（{agent.platform}）：{e.detail}",
            )

        # Hermes 返回了任务 ID 表示派发成功
        # 小白解释：Hermes 可能用 "id" 或 "task_id" 返回任务编号，这里两种都兼容。
        platform_task_id = result.get("task_id") or result.get("id")
        if platform_task_id:
            task.status = "Running"
            # V2 修复：用独立的 platform_task_id 字段存 Hermes 返回的任务 ID，
            # 不再用 result 字段（result 专门存任务执行结果，Webhook task_completed 时写入）
            task.platform_task_id = platform_task_id
        else:
            task.status = "Failed"
            task.ended_at = datetime.utcnow()

        # 第四步：更新 Agent 状态
        agent.status = "WORKING"
        agent.last_active_at = datetime.utcnow()

        # 第五步：事件日志
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

        # SSE 推送任务状态
        broadcast("task_status", {
            "taskId": task.id,
            "status": task.status,
            "event": "task_created",
        })

        return task_to_out(task)
    except HTTPException:
        raise
    except Exception as e:
        # 小白解释：兜底捕获，防止后端进程崩溃导致前端"Failed to fetch"
        print(f"[tasks.create_task] 未捕获异常: {e}")
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建任务时服务器内部错误：{e}")


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """查询单个任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="找不到该任务")
    return task_to_out(task)


@router.get("/{task_id}/logs", response_model=list[TaskLogOut])
async def get_task_logs(task_id: str, db: Session = Depends(get_db)):
    """
    获取任务执行日志
    小白解释：查看某个任务执行过程中的每一步记录
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="找不到该任务")

    logs = db.query(TaskLog).filter(
        TaskLog.task_id == task_id
    ).order_by(TaskLog.timestamp.asc()).all()
    return [task_log_to_out(l) for l in logs]
