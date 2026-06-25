"""
人才市场路由
负责 Agent 的发现与雇佣
相当于公司的"招聘网站"
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AgentMarketplace, OfficeAgent, AgentMapping, EventLog
from app.schemas import MarketplaceAgentOut, HireRequest
from app.adapters.hermes import hermes_adapter

# 创建路由器，前缀 /api/marketplace，标签用于 Swagger 文档分组
router = APIRouter(prefix="/api/marketplace", tags=["人才市场"])


@router.get("/agents", response_model=list[MarketplaceAgentOut])
async def list_marketplace_agents(db: Session = Depends(get_db)):
    """
    获取人才市场所有 Agent 列表
    小白解释：先看看本地数据库有没有 Agent，如果没有就去 Hermes 平台拉一批过来存好
    """
    # 第一步：从数据库查所有人才市场 Agent
    agents = db.query(AgentMarketplace).all()

    # 第二步：如果数据库为空，调用 Hermes 同步一批过来
    if not agents:
        # 调用 Hermes 发现 Agent（异步请求）
        remote_agents = await hermes_adapter.discover_agents()

        # 把远程拉到的 Agent 逐个存入数据库
        for item in remote_agents:
            agent = AgentMarketplace(
                id=item.get("id", f"market_{uuid.uuid4().hex[:8]}"),
                name=item.get("name", "未知 Agent"),
                avatar=item.get("avatar", ""),
                title=item.get("title", ""),
                platform=item.get("platform", "Hermes"),
                skills=item.get("skills", []),
                tools=item.get("tools", []),
                status=item.get("status", "ONLINE"),
                description=item.get("description", ""),
            )
            db.add(agent)

        db.commit()

        # 存完再查一次，拿到带完整字段的对象
        agents = db.query(AgentMarketplace).all()

    # 第三步：返回结果（MarketplaceAgentOut 字段与模型一致，可直接返回）
    return agents


@router.post("/hire")
async def hire_agent(req: HireRequest, db: Session = Depends(get_db)):
    """
    雇佣 Agent 进入办公室
    小白解释：从人才市场挑一个 Agent，给他安排工位，正式成为办公室员工
    """
    # 第一步：在人才市场找这个 Agent
    marketplace_agent = db.query(AgentMarketplace).filter(
        AgentMarketplace.id == req.agentId
    ).first()
    if not marketplace_agent:
        raise HTTPException(status_code=404, detail="人才市场中找不到该 Agent")

    # 第二步：检查是不是已经雇佣过了，避免重复入职
    existing = db.query(OfficeAgent).filter(
        OfficeAgent.marketplace_id == req.agentId
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该 Agent 已经被雇佣过了")

    # 第三步：创建办公室 Agent 记录（相当于办入职手续）
    office_agent_id = f"office_{uuid.uuid4().hex[:8]}"
    office_agent = OfficeAgent(
        id=office_agent_id,
        marketplace_id=marketplace_agent.id,
        name=marketplace_agent.name,
        avatar=marketplace_agent.avatar,
        title=marketplace_agent.title,
        platform=marketplace_agent.platform,
        platform_agent_id=marketplace_agent.id,
        status="ONLINE",
        hired_at=datetime.utcnow(),
        last_active_at=datetime.utcnow(),
        department="未分配",
        skills=marketplace_agent.skills,
        tools=marketplace_agent.tools,
        soul={},
        memory=[],
        performance={"totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0},
    )
    db.add(office_agent)

    # 第四步：创建平台映射记录（记录这个员工对应哪个平台的哪个 Agent）
    mapping = AgentMapping(
        office_agent_id=office_agent_id,
        platform=marketplace_agent.platform,
        platform_agent_id=marketplace_agent.id,
    )
    db.add(mapping)

    # 第五步：写一条事件日志，通知面板会显示"新员工入职"
    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="agent",
        title=f"新员工入职：{marketplace_agent.name}",
        description=f"从 {marketplace_agent.platform} 平台雇佣，职位：{marketplace_agent.title}",
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)

    db.commit()

    return {"message": "雇佣成功", "agentId": office_agent_id}
