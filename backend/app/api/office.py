"""
办公室 Agent 路由（V2 重写）
核心变更：
1. 列表接口返回 OfficeAgentListOut（精简版，不含 skills/tools/memory/performance，防 OOM）
2. 详情接口返回完整 OfficeAgentOut
3. 解雇时清理 AgentSkill 关联（cascade 自动处理）
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OfficeAgent, AgentMapping, EventLog, ChatMessage, Task
from app.schemas import OfficeAgentOut, OfficeAgentListOut

# 创建路由器
router = APIRouter(prefix="/api/office", tags=["办公室 Agent"])


def office_agent_to_out(agent: OfficeAgent) -> dict:
    """完整 Agent 详情（含 skills/tools/memory/performance/soul）"""
    return {
        "id": agent.id,
        "marketplaceId": agent.marketplace_id,
        "name": agent.name,
        "avatar": agent.avatar or "",
        "title": agent.title or "",
        "platform": agent.platform or "hermes",
        "platformAgentId": agent.platform_agent_id or "",
        "status": agent.status or "ONLINE",
        "hiredAt": agent.hired_at.isoformat() if agent.hired_at else None,
        "lastActiveAt": agent.last_active_at.isoformat() if agent.last_active_at else None,
        "department": agent.department or "未分配",
        "managerId": agent.manager_id,
        "soul": agent.soul or {},
        "skills": agent.skills or [],
        "tools": agent.tools or [],
        "memory": agent.memory or [],
        "performance": agent.performance or {
            "totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0
        },
    }


def office_agent_to_list_out(agent: OfficeAgent) -> dict:
    """
    精简列表项。
    小白解释：为了在首页/工具中心等列表页加载快，只返回少量字段。
    但 tools 是工具中心聚合统计必须的，所以保留。
    """
    return {
        "id": agent.id,
        "marketplaceId": agent.marketplace_id or "",
        "name": agent.name,
        "avatar": agent.avatar or "",
        "title": agent.title or "",
        "platform": agent.platform or "hermes",
        "platformAgentId": agent.platform_agent_id or "",
        "status": agent.status or "ONLINE",
        "department": agent.department or "未分配",
        "tools": agent.tools or [],
        "hiredAt": agent.hired_at.isoformat() if agent.hired_at else None,
        "lastActiveAt": agent.last_active_at.isoformat() if agent.last_active_at else None,
    }


@router.get("/agents", response_model=list[OfficeAgentListOut])
async def list_office_agents(db: Session = Depends(get_db)):
    """
    获取所有已雇佣 Agent 列表（精简版）
    小白解释：查看办公室里有哪些员工，只返回基本信息，不返回完整 skills/tools
    V2：用精简版防止 Agent 数量多时 OOM
    """
    agents = db.query(OfficeAgent).order_by(OfficeAgent.hired_at.desc()).all()
    return [office_agent_to_list_out(a) for a in agents]


@router.get("/agents/{agent_id}", response_model=OfficeAgentOut)
async def get_office_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    获取单个 Agent 详情（完整版）
    小白解释：查看某个员工的详细资料，包含技能、工具、记忆、绩效
    """
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")
    return office_agent_to_out(agent)


@router.delete("/agents/{agent_id}")
async def fire_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    解雇 Agent
    小白解释：把员工从办公室移除，同时清理映射关系和技能关联
    """
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    agent_name = agent.name

    # 删除平台映射
    db.query(AgentMapping).filter(AgentMapping.office_agent_id == agent_id).delete()
    # 删除关联的聊天记录（chat_history.agent_id 是 NOT NULL，必须手动清理）
    db.query(ChatMessage).filter(ChatMessage.agent_id == agent_id).delete()
    # 删除关联的任务（task.agent_id 也是 NOT NULL，否则也会触发外键错误）
    db.query(Task).filter(Task.agent_id == agent_id).delete()
    # AgentSkill 关联由 cascade="all, delete-orphan" 自动清理

    db.delete(agent)

    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="agent",
        title=f"员工离职：{agent_name}",
        description=f"Agent {agent_id} 已被解雇",
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)

    db.commit()

    return {"message": "解雇成功", "agentId": agent_id}
