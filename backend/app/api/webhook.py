"""
Webhook 路由
接收 Hermes 平台的事件回调
相当于公司的"通知接收器"，Hermes 那边有事就通知这边
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, OfficeAgent, EventLog
from app.schemas import WebhookPayload

# 创建路由器
router = APIRouter(prefix="/api/webhook", tags=["Webhook 回调"])


@router.post("/hermes")
async def hermes_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    """
    接收 Hermes 事件回调
    小白解释：Hermes 那边任务状态变了或者 Agent 上下线了，会主动通知我们，
    我们根据事件类型更新数据库，并记一条日志
    """
    event = payload.event
    title = ""
    description = ""

    # ===== 任务相关事件 =====
    if event in ("task_created", "task_started", "task_completed", "task_failed"):
        # 根据 task_id 查找任务
        task = None
        if payload.task_id:
            task = db.query(Task).filter(Task.id == payload.task_id).first()

        if task:
            # 根据事件类型更新任务状态
            status_map = {
                "task_created": "Pending",
                "task_started": "Running",
                "task_completed": "Completed",
                "task_failed": "Failed",
            }
            task.status = status_map.get(event, task.status)

            # 任务结束（完成或失败）时记录结束时间
            if event in ("task_completed", "task_failed"):
                task.ended_at = datetime.utcnow()
                if task.started_at:
                    # 计算耗时（分钟）
                    delta = task.ended_at - task.started_at
                    task.duration = int(delta.total_seconds() // 60)

                # 更新 Agent 状态和绩效
                agent = db.query(OfficeAgent).filter(
                    OfficeAgent.id == task.agent_id
                ).first()
                if agent:
                    agent.status = "ONLINE"
                    perf = agent.performance or {
                        "totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0
                    }
                    perf["totalTasks"] = perf.get("totalTasks", 0) + 1
                    if event == "task_completed":
                        perf["successTasks"] = perf.get("successTasks", 0) + 1
                    else:
                        perf["failedTasks"] = perf.get("failedTasks", 0) + 1
                    agent.performance = perf

            title = f"任务{event.replace('task_', '')}：{task.name}"
            description = f"任务 ID：{task.id}，状态：{task.status}"
        else:
            title = f"任务事件：{event}"
            description = f"任务 ID：{payload.task_id}（本地未找到）"

    # ===== Agent 上下线事件 =====
    elif event in ("agent_online", "agent_offline"):
        # 根据 agent_id 查找办公室 Agent
        agent = None
        if payload.agent_id:
            agent = db.query(OfficeAgent).filter(
                OfficeAgent.platform_agent_id == payload.agent_id
            ).first()

        if agent:
            # 更新 Agent 状态
            agent.status = "ONLINE" if event == "agent_online" else "OFFLINE"
            title = f"Agent {'上线' if event == 'agent_online' else '下线'}：{agent.name}"
            description = f"平台 Agent ID：{payload.agent_id}"
        else:
            title = f"Agent 事件：{event}"
            description = f"平台 Agent ID：{payload.agent_id}（本地未找到）"

    # ===== 未知事件 =====
    else:
        title = f"未知事件：{event}"
        description = f"payload：{payload.model_dump()}"

    # 写一条事件日志
    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="task" if event.startswith("task_") else "agent",
        title=title,
        description=description,
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)

    db.commit()

    return {"message": "回调已处理", "event": event}
