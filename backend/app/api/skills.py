"""
Skill 管理路由（V2 新增）
管理 Agent 的技能：查看、添加、启停、配置、刷新
相当于公司的"员工技能管理后台"
核心设计：
1. Skill 是平台级实体（一张 skill 目录表），多个 Agent 可共享同一个 Skill
2. AgentSkill 是关联表，记录"哪个 Agent 启用了哪个 Skill"及参数、使用次数
3. 刷新接口调用 Adapter.get_skills() 从源平台同步最新技能
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OfficeAgent, Skill, AgentSkill
from app.schemas import (
    SkillOut,
    AgentSkillOut,
    AgentSkillAddRequest,
    AgentSkillUpdateRequest,
)
from app.adapters import get_adapter_or_raise
from app.adapters.base import AdapterError

# 创建路由器
router = APIRouter(prefix="/api", tags=["Skill 技能管理"])


def skill_to_out(skill: Skill) -> dict:
    """把 Skill 数据库模型转成响应字典（下划线 → 驼峰）"""
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description or "",
        "paramsSchema": skill.params_schema or {},
        "requiredTools": skill.required_tools or [],
        "sourcePlatform": skill.source_platform or "hermes",
        "createdAt": skill.created_at.isoformat() if skill.created_at else None,
    }


def agent_skill_to_out(asoc: AgentSkill) -> dict:
    """把 AgentSkill 关联模型转成响应字典（附带 Skill 名称和描述）"""
    return {
        "id": asoc.id,
        "agentId": asoc.agent_id,
        "skillId": asoc.skill_id,
        "skillName": asoc.skill.name if asoc.skill else "",
        "skillDescription": asoc.skill.description if asoc.skill else "",
        "enabled": asoc.enabled,
        "params": asoc.params or {},
        "lastUsedAt": asoc.last_used_at.isoformat() if asoc.last_used_at else None,
        "useCount": asoc.use_count or 0,
    }


# ===== Skill 目录查询 =====

@router.get("/skills", response_model=list[SkillOut])
async def list_skills(db: Session = Depends(get_db)):
    """
    获取平台级 Skill 目录
    小白解释：查看办公室里所有可用的技能清单
    """
    skills = db.query(Skill).order_by(Skill.created_at.desc()).all()
    return [skill_to_out(s) for s in skills]


@router.get("/skills/{skill_id}", response_model=SkillOut)
async def get_skill(skill_id: str, db: Session = Depends(get_db)):
    """查询单个 Skill 详情"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="找不到该 Skill")
    return skill_to_out(skill)


# ===== Agent-Skill 关联管理 =====

@router.get("/agents/{agent_id}/skills", response_model=list[AgentSkillOut])
async def list_agent_skills(agent_id: str, db: Session = Depends(get_db)):
    """
    获取某个 Agent 已配置的技能列表
    小白解释：查看某个员工会哪些技能、哪些开着、用了多少次
    """
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    items = db.query(AgentSkill).filter(AgentSkill.agent_id == agent_id).all()
    return [agent_skill_to_out(a) for a in items]


@router.post("/agents/{agent_id}/skills", response_model=AgentSkillOut)
async def add_agent_skill(
    agent_id: str, req: AgentSkillAddRequest, db: Session = Depends(get_db)
):
    """
    给 Agent 添加一个 Skill
    小白解释：给员工分配一项新技能，可以附带参数配置
    """
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    skill = db.query(Skill).filter(Skill.id == req.skillId).first()
    if not skill:
        raise HTTPException(status_code=404, detail="找不到该 Skill")

    # 检查是否已添加过
    existing = db.query(AgentSkill).filter(
        AgentSkill.agent_id == agent_id,
        AgentSkill.skill_id == req.skillId,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该 Agent 已配置此 Skill")

    asoc = AgentSkill(
        id=f"as_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        skill_id=req.skillId,
        enabled=True,
        params=req.params or {},
        use_count=0,
    )
    db.add(asoc)
    db.commit()
    db.refresh(asoc)
    return agent_skill_to_out(asoc)


@router.put("/agents/{agent_id}/skills/{skill_id}", response_model=AgentSkillOut)
async def update_agent_skill(
    agent_id: str,
    skill_id: str,
    req: AgentSkillUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    修改 Agent 的 Skill 配置（启停或改参数）
    小白解释：开关某个技能，或者调整技能的参数
    """
    asoc = db.query(AgentSkill).filter(
        AgentSkill.agent_id == agent_id,
        AgentSkill.skill_id == skill_id,
    ).first()
    if not asoc:
        raise HTTPException(status_code=404, detail="找不到该 Agent-Skill 关联")

    if req.enabled is not None:
        asoc.enabled = req.enabled
    if req.params is not None:
        asoc.params = req.params

    db.commit()
    db.refresh(asoc)
    return agent_skill_to_out(asoc)


@router.delete("/agents/{agent_id}/skills/{skill_id}")
async def remove_agent_skill(
    agent_id: str, skill_id: str, db: Session = Depends(get_db)
):
    """移除 Agent 的某个 Skill"""
    asoc = db.query(AgentSkill).filter(
        AgentSkill.agent_id == agent_id,
        AgentSkill.skill_id == skill_id,
    ).first()
    if not asoc:
        raise HTTPException(status_code=404, detail="找不到该 Agent-Skill 关联")

    db.delete(asoc)
    db.commit()
    return {"message": "已移除 Skill", "agentId": agent_id, "skillId": skill_id}


# ===== 从源平台同步 Skill =====

@router.post("/agents/{agent_id}/skills/refresh")
async def refresh_agent_skills(agent_id: str, db: Session = Depends(get_db)):
    """
    从源平台刷新该 Agent 的技能列表
    小白解释：调用 Hermes 接口拉取该 Agent 最新拥有的技能，
    新增的写入 Skill 目录 + 建立 AgentSkill 关联，已有的跳过
    """
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    try:
        adapter = get_adapter_or_raise(agent.platform)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    try:
        remote_skills = await adapter.get_skills(agent.platform_agent_id or agent.id)
    except AdapterError as e:
        raise HTTPException(
            status_code=502,
            detail=f"获取 Skill 失败（{agent.platform}）：{e.detail}",
        )

    # remote_skills 的每一项是 dict：{id, name, description, params_schema, required_tools}
    added = []
    for item in remote_skills:
        if isinstance(item, str):
            # 兼容旧格式：纯字符串自动转 dict
            item = {"id": item, "name": item, "description": ""}

        skill_id = item.get("id") or item.get("name", "")
        if not skill_id:
            continue

        # 写入或更新 Skill 目录
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            skill = Skill(
                id=skill_id,
                name=item.get("name", skill_id),
                description=item.get("description", ""),
                params_schema=item.get("params_schema", {}) or item.get("paramsSchema", {}),
                required_tools=item.get("required_tools", []) or item.get("requiredTools", []),
                source_platform=agent.platform,
            )
            db.add(skill)
        else:
            # 已存在则更新描述（不覆盖参数配置）
            if item.get("description"):
                skill.description = item["description"]

        # 建立 AgentSkill 关联（已存在则跳过）
        existing = db.query(AgentSkill).filter(
            AgentSkill.agent_id == agent_id,
            AgentSkill.skill_id == skill_id,
        ).first()
        if not existing:
            asoc = AgentSkill(
                id=f"as_{uuid.uuid4().hex[:8]}",
                agent_id=agent_id,
                skill_id=skill_id,
                enabled=True,
                params={},
                use_count=0,
            )
            db.add(asoc)
            added.append(skill_id)

    db.commit()
    return {
        "message": "Skill 同步完成",
        "agentId": agent_id,
        "totalRemote": len(remote_skills),
        "added": added,
    }
