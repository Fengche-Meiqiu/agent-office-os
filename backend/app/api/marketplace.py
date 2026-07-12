"""
人才市场路由（V2 重写）
核心变更：
1. 去掉 if not agents 懒同步，改为 POST /sync 主动同步
2. 同步时正确写入 platform_agent_id（源平台真实 ID），不用 marketplace.id
3. 雇佣时 platform_agent_id 取 marketplace.platform_agent_id（而非 marketplace.id）
4. 使用 get_adapter 路由，不硬编码 hermes_adapter
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AgentMarketplace, OfficeAgent, AgentMapping, EventLog
from app.schemas import MarketplaceAgentOut, HireRequest
from app.adapters import get_adapter_or_raise
from app.adapters.base import AdapterError


def _build_soul_from_profile(profile: dict | None) -> dict:
    """
    从 Hermes 的 Agent 详情中解析 Soul（人格）数据。
    小白解释：Hermes 目前可能不返回 soul，但能返回 identity/goal/principles 等字段时，
    我们自动拼成 soul 对象存到本地。如果都没有，返回空对象，前端会显示"待上线"。
    """
    if not profile or not isinstance(profile, dict):
        return {}
    # Hermes 可能直接给 soul 对象
    if "soul" in profile and isinstance(profile["soul"], dict):
        return {
            "identity": profile["soul"].get("identity", ""),
            "goal": profile["soul"].get("goal", ""),
            "principles": profile["soul"].get("principles", ""),
            "style": profile["soul"].get("style", ""),
            "description": profile["soul"].get("description", ""),
        }
    # 兼容：Hermes 把人格字段打散在顶层
    keys = ["identity", "goal", "principles", "style", "personality"]
    if any(k in profile for k in keys):
        return {
            "identity": profile.get("identity", ""),
            "goal": profile.get("goal", ""),
            "principles": profile.get("principles", ""),
            "style": profile.get("style", profile.get("personality", "")),
            "description": profile.get("description", ""),
        }
    return {}

# 创建路由器
router = APIRouter(prefix="/api/marketplace", tags=["人才市场"])


def marketplace_agent_to_out(a: AgentMarketplace) -> dict:
    """数据库模型 → 响应字典（驼峰风格）"""
    return {
        "id": a.id,
        "name": a.name,
        "avatar": a.avatar or "",
        "title": a.title or "",
        "platform": a.platform or "hermes",
        "platformAgentId": a.platform_agent_id or "",
        "skills": a.skills or [],
        "tools": a.tools or [],
        "status": a.status or "ONLINE",
        "description": a.description or "",
        "soul": a.soul or {},
    }


@router.get("/agents", response_model=list[MarketplaceAgentOut])
async def list_marketplace_agents(db: Session = Depends(get_db)):
    """
    获取人才市场所有 Agent 列表
    小白解释：只查本地数据库，不再自动同步。
    需要同步时调用 POST /api/marketplace/sync
    """
    agents = db.query(AgentMarketplace).filter(
        AgentMarketplace.platform == "hermes"
    ).order_by(AgentMarketplace.created_at.desc()).all()
    return [marketplace_agent_to_out(a) for a in agents]


@router.post("/sync")
async def sync_marketplace_agents(db: Session = Depends(get_db)):
    """
    主动从源平台同步 Agent 到人才市场
    小白解释：点一下"刷新人才库"按钮，从 Hermes 拉取最新 Agent 列表
    V2 修复：platform_agent_id 存源平台真实 ID
    """
    adapter = get_adapter_or_raise("hermes")
    try:
        remote_agents = await adapter.discover_agents()
    except AdapterError as e:
        raise HTTPException(
            status_code=502,
            detail=f"同步失败（{adapter.platform_name}）：{e.detail}",
        )

    added = []
    updated = 0
    for item in remote_agents:
        # 优先用源平台 ID 去重
        platform = str(item.get("platform", "hermes")).lower()
        platform_id = item.get("platform_agent_id") or item.get("id", "")
        if platform != "hermes" or not platform_id:
            continue

        # 查是否已存在（按 platform_agent_id 查）
        existing = db.query(AgentMarketplace).filter(
            AgentMarketplace.platform_agent_id == platform_id
        ).first()

        # 尝试从 Hermes 获取完整 Agent 详情，以拿到 soul 等字段
        profile = None
        try:
            profile = await adapter.get_profile(platform_id)
        except Exception:
            profile = None

        soul = _build_soul_from_profile(profile)

        # 小白解释：同步时尽量从 Hermes 拉取 skills/tools，并规范化为字符串列表。
        # discover_agents 可能只给简略字段，这里用专门的接口补全。
        skills = item.get("skills", [])
        tools = item.get("tools", [])
        try:
            remote_skills = await adapter.get_skills(platform_id)
            skills = [s.get("name") or s.get("id") or str(s) for s in remote_skills]
        except Exception:
            pass
        try:
            remote_tools = await adapter.get_tools(platform_id)
            tools = [t.get("name") or str(t) for t in remote_tools]
        except Exception:
            pass

        if existing:
            # 已存在，更新信息
            existing.name = item.get("name", existing.name)
            existing.title = item.get("title", existing.title)
            existing.avatar = item.get("avatar", existing.avatar)
            existing.skills = skills or existing.skills
            existing.tools = tools or existing.tools
            existing.description = item.get("description", existing.description)
            existing.status = item.get("status", existing.status)
            existing.soul = soul
            updated += 1
        else:
            # 新增
            agent = AgentMarketplace(
                id=item.get("id", f"market_{uuid.uuid4().hex[:8]}"),
                name=item.get("name", "未知 Agent"),
                avatar=item.get("avatar", ""),
                title=item.get("title", ""),
                platform="hermes",
                platform_agent_id=platform_id,
                skills=skills,
                tools=tools,
                status=item.get("status", "ONLINE"),
                description=item.get("description", ""),
                soul=soul,
            )
            db.add(agent)
            added.append(agent.name)

    db.commit()

    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="agent",
        title="人才市场同步",
        description=f"新增 {len(added)} 个，更新 {updated} 个",
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)
    db.commit()

    return {
        "message": "同步完成",
        "added": added,
        "updated": updated,
        "total": db.query(AgentMarketplace).count(),
    }


@router.post("/hire")
async def hire_agent(req: HireRequest, db: Session = Depends(get_db)):
    """
    雇佣 Agent 进入办公室
    小白解释：从人才市场挑一个 Agent，办入职手续
    V2 修复：platform_agent_id 用 marketplace.platform_agent_id（源平台真实 ID）
    """
    marketplace_agent = db.query(AgentMarketplace).filter(
        AgentMarketplace.id == req.agentId
    ).first()
    if not marketplace_agent:
        raise HTTPException(status_code=404, detail="人才市场中找不到该 Agent")

    # 检查是否已雇佣
    existing = db.query(OfficeAgent).filter(
        OfficeAgent.marketplace_id == req.agentId
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该 Agent 已经被雇佣过了")

    office_agent_id = f"office_{uuid.uuid4().hex[:8]}"
    # V2 关键修复：用 marketplace.platform_agent_id 而非 marketplace.id
    platform_agent_id = marketplace_agent.platform_agent_id or marketplace_agent.id

    # 尝试从 Hermes 拉取完整人格数据和记忆
    adapter = get_adapter_or_raise(marketplace_agent.platform)
    profile = None
    memory_summary = ""
    try:
        profile = await adapter.get_profile(platform_agent_id)
    except Exception:
        profile = None
    try:
        memory_data = await adapter.get_memory(platform_agent_id)
        if memory_data and isinstance(memory_data, dict):
            memory_summary = memory_data.get("summary", "")
    except Exception:
        memory_summary = ""

    memory = []
    if memory_summary:
        memory.append(memory_summary)

    office_agent = OfficeAgent(
        id=office_agent_id,
        marketplace_id=marketplace_agent.id,
        name=marketplace_agent.name,
        avatar=marketplace_agent.avatar,
        title=marketplace_agent.title,
        platform=marketplace_agent.platform,
        platform_agent_id=platform_agent_id,
        status="ONLINE",
        hired_at=datetime.utcnow(),
        last_active_at=datetime.utcnow(),
        department="未分配",
        skills=marketplace_agent.skills,
        tools=marketplace_agent.tools,
        soul=marketplace_agent.soul or _build_soul_from_profile(profile),
        memory=memory,
        performance={"totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0},
    )
    db.add(office_agent)

    # 创建平台映射记录
    mapping = AgentMapping(
        office_agent_id=office_agent_id,
        platform=marketplace_agent.platform,
        platform_agent_id=platform_agent_id,
    )
    db.add(mapping)

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
