"""
办公室 Agent 路由
管理已雇佣员工的查询、详情、解雇
相当于公司的"员工管理后台"
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OfficeAgent, AgentMapping, EventLog
from app.schemas import OfficeAgentOut
from app.adapters.hermes import hermes_adapter

# 创建路由器
router = APIRouter(prefix="/api/office", tags=["办公室 Agent"])


def office_agent_to_out(agent: OfficeAgent) -> dict:
    """
    把数据库模型转成响应字典
    小白解释：数据库里字段名是下划线风格（如 marketplace_id），
    前端要的是驼峰风格（如 marketplaceId），这里做一下转换
    """
    return {
        "id": agent.id,
        "marketplaceId": agent.marketplace_id,
        "name": agent.name,
        "avatar": agent.avatar,
        "title": agent.title,
        "platform": agent.platform,
        "platformAgentId": agent.platform_agent_id,
        "status": agent.status,
        "hiredAt": agent.hired_at.isoformat() if agent.hired_at else None,
        "lastActiveAt": agent.last_active_at.isoformat() if agent.last_active_at else None,
        "department": agent.department,
        "managerId": agent.manager_id,
        "soul": agent.soul or {},
        "skills": agent.skills or [],
        "tools": agent.tools or [],
        "memory": agent.memory or [],
        "performance": agent.performance or {
            "totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0
        },
    }


@router.get("/agents", response_model=list[OfficeAgentOut])
async def list_office_agents(db: Session = Depends(get_db)):
    """
    获取所有已雇佣 Agent 列表
    小白解释：查看办公室里现在有哪些员工
    """
    agents = db.query(OfficeAgent).all()
    # 手动转换字段名（驼峰风格）
    return [office_agent_to_out(a) for a in agents]


@router.get("/agents/{agent_id}", response_model=OfficeAgentOut)
async def get_office_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    获取单个 Agent 详情
    小白解释：查看某个员工的详细资料
    """
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")
    return office_agent_to_out(agent)


@router.delete("/agents/{agent_id}")
async def fire_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    解雇 Agent
    小白解释：把员工从办公室移除，同时清理映射关系，并记一条日志
    """
    # 第一步：找到这个 Agent
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    agent_name = agent.name

    # 第二步：删除平台映射记录
    db.query(AgentMapping).filter(AgentMapping.office_agent_id == agent_id).delete()

    # 第三步：删除办公室 Agent 记录
    db.delete(agent)

    # 第四步：写一条事件日志
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
