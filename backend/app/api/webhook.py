"""
Webhook 路由（V2 重写）
接收 Hermes 平台的事件回调，是"Hermes → Office OS"实时通道的入口
核心变更：
1. task_completed/task_failed 时存储 result 到 Task 表，并自动创建 Output 成果
2. 新增 task_progress（进度更新）和 task_step（步骤日志）事件处理
3. 所有任务事件通过 SSE broadcast 实时推送给前端
4. Agent 上下线事件也通过 SSE 推送
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, TaskLog, OfficeAgent, Output, EventLog
from app.schemas import WebhookPayload
from app.api.sse import broadcast

# 创建路由器
router = APIRouter(prefix="/api/webhook", tags=["Webhook 回调"])


@router.post("/hermes")
async def hermes_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    """
    接收 Hermes 事件回调
    小白解释：Hermes 那边任务状态变了、有进度了、Agent 上下线了，
    都会主动 POST 到这个接口，我们更新数据库 + 推 SSE 给前端
    """
    event = payload.event
    title = ""
    description = ""

    # ===== 任务状态事件 =====
    if event in ("task_created", "task_started", "task_completed", "task_failed"):
        task = None
        if payload.task_id:
            # 小白解释：Hermes 回调里的 task_id 是 Hermes 平台的任务 ID，
            # 我们本地存在 platform_task_id 字段里。优先用这个字段匹配。
            task = db.query(Task).filter(
                (Task.platform_task_id == payload.task_id) | (Task.id == payload.task_id)
            ).first()

        if task:
            # 状态映射
            status_map = {
                "task_created": "Pending",
                "task_started": "Running",
                "task_completed": "Completed",
                "task_failed": "Failed",
            }
            task.status = status_map.get(event, task.status)

            # 存储 Hermes 返回的结果
            if payload.result and event in ("task_completed", "task_failed"):
                task.result = payload.result

                # 任务完成时自动创建 Output 成果
                if event == "task_completed":
                    output_id = f"output_{uuid.uuid4().hex[:8]}"
                    output = Output(
                        id=output_id,
                        name=f"任务成果 - {task.name}",
                        type="markdown",
                        source="task",
                        content=payload.result,
                    )
                    db.add(output)
                    task.output_id = output_id

            # 任务结束时记录结束时间 + 耗时
            if event in ("task_completed", "task_failed"):
                task.ended_at = datetime.utcnow()
                if task.started_at:
                    delta = task.ended_at - task.started_at
                    task.duration = int(delta.total_seconds() // 60)

                # 恢复 Agent 状态 + 更新绩效
                agent = db.query(OfficeAgent).filter(
                    OfficeAgent.id == task.agent_id
                ).first()
                if agent:
                    agent.status = "ONLINE"
                    perf = agent.performance or {
                        "totalTasks": 0, "successTasks": 0,
                        "failedTasks": 0, "meetingCount": 0,
                    }
                    perf["totalTasks"] = perf.get("totalTasks", 0) + 1
                    if event == "task_completed":
                        perf["successTasks"] = perf.get("successTasks", 0) + 1
                    else:
                        perf["failedTasks"] = perf.get("failedTasks", 0) + 1
                    agent.performance = perf

            # SSE 推送任务状态变更
            broadcast("task_status", {
                "taskId": task.id,
                "status": task.status,
                "result": payload.result,
                "event": event,
            })

            title = f"任务{event.replace('task_', '')}：{task.name}"
            description = f"任务 ID：{task.id}，状态：{task.status}"
        else:
            title = f"任务事件：{event}"
            description = f"任务 ID：{payload.task_id}（本地未找到）"

    # ===== 任务进度事件（V2 新增）=====
    elif event == "task_progress":
        task = None
        if payload.task_id:
            task = db.query(Task).filter(
                (Task.platform_task_id == payload.task_id) | (Task.id == payload.task_id)
            ).first()

        if task:
            # 更新进度
            if payload.progress is not None:
                task.progress = max(0, min(100, payload.progress))
            if payload.step:
                task.current_step = payload.step

            # SSE 推送进度
            broadcast("task_progress", {
                "taskId": task.id,
                "progress": task.progress,
                "currentStep": task.current_step,
            })

            title = f"任务进度更新：{task.name}"
            description = f"进度：{task.progress}%，步骤：{task.current_step or ''}"
        else:
            title = f"任务进度事件：{event}"
            description = f"任务 ID：{payload.task_id}（未找到）"

    # ===== 任务步骤日志事件（V2 新增）=====
    elif event == "task_step":
        task = None
        if payload.task_id:
            task = db.query(Task).filter(
                (Task.platform_task_id == payload.task_id) | (Task.id == payload.task_id)
            ).first()

        if task:
            # 写入 TaskLog 表
            log = TaskLog(
                id=f"log_{uuid.uuid4().hex[:8]}",
                task_id=task.id,
                step=payload.step or "",
                detail=payload.detail or "",
                level="info",
            )
            db.add(log)

            # 更新当前步骤
            if payload.step:
                task.current_step = payload.step

            # SSE 推送步骤日志
            broadcast("task_step", {
                "taskId": task.id,
                "step": payload.step or "",
                "detail": payload.detail or "",
            })

            title = f"任务步骤：{payload.step or ''}"
            description = payload.detail or ""
        else:
            title = f"任务步骤事件：{event}"
            description = f"任务 ID：{payload.task_id}（未找到）"

    # ===== Agent 上下线事件 =====
    elif event in ("agent_online", "agent_offline"):
        agent = None
        if payload.agent_id:
            # 通过 platform_agent_id 查找
            agent = db.query(OfficeAgent).filter(
                OfficeAgent.platform_agent_id == payload.agent_id
            ).first()

        if agent:
            agent.status = "ONLINE" if event == "agent_online" else "OFFLINE"
            # SSE 推送 Agent 状态
            broadcast("agent_status", {
                "agentId": agent.id,
                "status": agent.status,
            })
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

