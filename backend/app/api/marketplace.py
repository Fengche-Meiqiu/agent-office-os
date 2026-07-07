import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.hermes import hermes_adapter
from app.database import get_db
from app.models import AgentMapping, AgentMarketplace, EventLog, OfficeAgent
from app.schemas import HireRequest, MarketplaceAgentOut

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


def _upsert_marketplace_agent(db: Session, item: dict) -> AgentMarketplace:
    agent_id = item.get("id") or f"market_{uuid.uuid4().hex[:8]}"
    agent = db.query(AgentMarketplace).filter(AgentMarketplace.id == agent_id).first()
    if not agent:
        agent = AgentMarketplace(id=agent_id)
        db.add(agent)

    agent.name = item.get("name") or "Unnamed Hermes Agent"
    agent.avatar = item.get("avatar") or ""
    agent.title = item.get("title") or "Needs Hermes completion"
    agent.platform = item.get("platform") or "Hermes"
    agent.skills = item.get("skills") or []
    agent.tools = item.get("tools") or []
    agent.status = item.get("status") or "OFFLINE"
    agent.description = item.get("description") or "Needs Hermes completion"
    return agent


async def sync_agents_from_hermes(db: Session) -> int:
    remote_agents = await hermes_adapter.discover_agents()
    for item in remote_agents:
        _upsert_marketplace_agent(db, item)
    db.commit()
    return len(remote_agents)


@router.get("/agents", response_model=list[MarketplaceAgentOut])
async def list_marketplace_agents(db: Session = Depends(get_db)):
    await sync_agents_from_hermes(db)
    return db.query(AgentMarketplace).order_by(AgentMarketplace.name.asc()).all()


@router.post("/sync")
async def sync_marketplace_agents(db: Session = Depends(get_db)):
    count = await sync_agents_from_hermes(db)
    return {"message": "sync completed", "count": count}


@router.post("/hire")
async def hire_agent(req: HireRequest, db: Session = Depends(get_db)):
    marketplace_agent = db.query(AgentMarketplace).filter(AgentMarketplace.id == req.agentId).first()
    if not marketplace_agent:
        raise HTTPException(status_code=404, detail="Agent not found in marketplace")

    existing = db.query(OfficeAgent).filter(OfficeAgent.marketplace_id == req.agentId).first()
    if existing:
        return {"message": "agent already hired", "agentId": existing.id, "officeAgentId": existing.id}

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
        department="Unassigned",
        skills=marketplace_agent.skills,
        tools=marketplace_agent.tools,
        soul={
            "identity": marketplace_agent.title,
            "goal": "Complete user work through Agent Office OS.",
            "principles": "Reliable, transparent, and task-oriented.",
            "style": "Concise and professional.",
            "description": marketplace_agent.description,
        },
        memory=[f"Synced from {marketplace_agent.platform}"],
        performance={"totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0},
    )
    db.add(office_agent)
    db.add(AgentMapping(office_agent_id=office_agent_id, platform=marketplace_agent.platform, platform_agent_id=marketplace_agent.id))
    db.add(EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="agent",
        title=f"Agent hired: {marketplace_agent.name}",
        description=f"Source: {marketplace_agent.platform}; role: {marketplace_agent.title}",
        timestamp=datetime.utcnow(),
    ))
    db.commit()
    return {"message": "agent hired", "agentId": office_agent_id, "officeAgentId": office_agent_id}
