"""
会议路由（V2 重构：自由讨论，去掉固定轮次）
核心变更：
1. rounds(嵌套) → messages(扁平)
2. 去掉 MAX_ROUNDS 和 next_round
3. 新增 start / ask-all / ask-{agent_id} 路由
4. 主持人可随时结束会议
5. 所有发言通过 SSE 实时推送
6. 用 get_adapter 路由，不再硬编码 hermes_adapter
7. 用 resolve_platform_id 统一身份映射
"""
import asyncio
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Meeting, OfficeAgent, Output, EventLog
from app.schemas import (
    MeetingOut,
    MeetingCreateRequest,
    MeetingMessageRequest,
)
from app.adapters import get_adapter_or_raise
from app.adapters.base import AdapterError
from app.api.sse import broadcast

router = APIRouter(prefix="/api/meetings", tags=["会议管理"])


def resolve_platform_id(agent: OfficeAgent, db: Session) -> str:
    """
    统一身份映射：查 AgentMapping 表获取真实 platform_agent_id
    解决上一轮两套 ID 体系断裂问题
    """
    from app.models import AgentMapping

    mapping = db.query(AgentMapping).filter(
        AgentMapping.office_agent_id == agent.id
    ).first()
    if mapping and mapping.platform_agent_id:
        return mapping.platform_agent_id
    if agent.platform_agent_id:
        return agent.platform_agent_id
    return agent.id


def meeting_to_out(meeting: Meeting) -> dict:
    """数据库模型 → 响应字典（messages 替代 rounds）"""
    return {
        "id": meeting.id,
        "topic": meeting.topic,
        "agentIds": meeting.agent_ids or [],
        "status": meeting.status,
        "messages": meeting.messages or [],
        "summary": meeting.summary,
        "decisions": meeting.decisions or [],
        "actions": meeting.actions or [],
        "createdAt": meeting.created_at.isoformat() if meeting.created_at else None,
    }


def build_history(messages: list) -> list:
    """把已有消息整理成 Hermes 需要的历史记录"""
    history = []
    for m in messages:
        history.append({
            "role": m.get("role", "agent"),
            "content": m.get("content", ""),
            "agentName": m.get("agentName", ""),
        })
    return history


async def _agent_speak(
    agent: OfficeAgent, meeting: Meeting, history: list, db: Session
) -> dict | None:
    """
    让单个 Agent 在会议中发言（内部方法）
    返回发言消息 dict，失败返回 None
    """
    platform_id = resolve_platform_id(agent, db)
    try:
        adapter = get_adapter_or_raise(agent.platform)
    except ValueError as e:
        return {
            "role": "agent",
            "agentId": agent.id,
            "agentName": agent.name,
            "content": f"（{agent.name} 暂时无法响应：{e}）",
            "timestamp": datetime.utcnow().isoformat(),
        }
    try:
        result = await adapter.meeting_respond(
            platform_id, meeting.id, meeting.topic, history
        )
        opinion = result.get("opinion", "（暂无意见）")
    except AdapterError as e:
        opinion = f"（{agent.name} 暂时无法响应：{e.detail}）"

    msg = {
        "role": "agent",
        "agentId": agent.id,
        "agentName": agent.name,
        "content": opinion,
        "timestamp": datetime.utcnow().isoformat(),
    }
    return msg


async def _speak_all_agents(
    meeting: Meeting, db: Session
) -> list[dict]:
    """
    让所有参会 Agent 并行发言（V2 性能优化）
    小白解释：原来是一个一个等 Agent 发言（串行），现在用 asyncio.gather
    让所有 Agent 同时发言（并行），大幅减少等待时间
    返回按 agent_ids 顺序排列的消息列表
    """
    # 先查出所有参会 Agent
    agents: list[OfficeAgent] = []
    for aid in meeting.agent_ids:
        agent = db.query(OfficeAgent).filter(
            (OfficeAgent.id == aid) | (OfficeAgent.platform_agent_id == aid)
        ).first()
        if agent:
            agents.append(agent)

    if not agents:
        return []

    # 构建历史记录
    history = build_history(meeting.messages or [])

    # 并行调用所有 Agent 发言（asyncio.gather 保留顺序）
    tasks = [_agent_speak(agent, meeting, history, db) for agent in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 收集成功的消息（按 agents 顺序）
    messages: list[dict] = []
    for agent, result in zip(agents, results):
        if isinstance(result, Exception):
            # 某个 Agent 发言失败，用降级文案替代（不污染数据）
            msg = {
                "role": "agent",
                "agentId": agent.id,
                "agentName": agent.name,
                "content": f"（{agent.name} 暂时无法响应）",
                "timestamp": datetime.utcnow().isoformat(),
            }
            messages.append(msg)
        elif result is not None:
            messages.append(result)

    return messages


@router.get("", response_model=list[MeetingOut])
async def list_meetings(db: Session = Depends(get_db)):
    """获取所有会议列表"""
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [meeting_to_out(m) for m in meetings]


@router.post("", response_model=MeetingOut)
async def create_meeting(req: MeetingCreateRequest, db: Session = Depends(get_db)):
    """创建新会议（选择 2-10 个 Agent + 主题）"""
    for aid in req.agentIds:
        agent = db.query(OfficeAgent).filter(
            (OfficeAgent.id == aid) | (OfficeAgent.platform_agent_id == aid)
        ).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"参会 Agent 不存在：{aid}")

    meeting_id = f"meeting_{uuid.uuid4().hex[:8]}"
    meeting = Meeting(
        id=meeting_id,
        topic=req.topic,
        agent_ids=req.agentIds,
        status="created",
        messages=[],
    )
    db.add(meeting)

    for aid in req.agentIds:
        agent = db.query(OfficeAgent).filter(
            (OfficeAgent.id == aid) | (OfficeAgent.platform_agent_id == aid)
        ).first()
        if agent:
            agent.status = "MEETING"

    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="meeting",
        title=f"新会议创建：{req.topic}",
        description=f"参会人数：{len(req.agentIds)} 人",
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)

    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """获取会议详情"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/start", response_model=MeetingOut)
async def start_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """开始会议：所有参会 Agent 首次发言"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")
    if meeting.status != "created":
        raise HTTPException(status_code=400, detail="会议已开始，无法重复开始")

    meeting.status = "running"

    # V2 优化：并行让所有 Agent 发言（原来是串行 for 循环）
    messages = await _speak_all_agents(meeting, db)
    for msg in messages:
        meeting.messages.append(msg)
        broadcast("meeting_message", {"meeting_id": meeting.id, "message": msg})

    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/ask-all", response_model=MeetingOut)
async def ask_all(meeting_id: str, db: Session = Depends(get_db)):
    """让所有参会 Agent 发言"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")
    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="会议已结束")

    if meeting.status == "created":
        meeting.status = "running"

    # V2 优化：并行让所有 Agent 发言（原来是串行 for 循环）
    messages = await _speak_all_agents(meeting, db)
    for msg in messages:
        meeting.messages.append(msg)
        broadcast("meeting_message", {"meeting_id": meeting.id, "message": msg})

    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/ask/{agent_id}", response_model=MeetingOut)
async def ask_agent(meeting_id: str, agent_id: str, db: Session = Depends(get_db)):
    """让指定 Agent 发言"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")
    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="会议已结束")

    agent = db.query(OfficeAgent).filter(
        (OfficeAgent.id == agent_id) | (OfficeAgent.platform_agent_id == agent_id)
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    if meeting.status == "created":
        meeting.status = "running"

    history = build_history(meeting.messages or [])
    msg = await _agent_speak(agent, meeting, history, db)
    if msg:
        meeting.messages.append(msg)
        broadcast("meeting_message", {"meeting_id": meeting.id, "message": msg})

    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/messages", response_model=MeetingOut)
async def add_meeting_message(
    meeting_id: str, req: MeetingMessageRequest, db: Session = Depends(get_db)
):
    """主持人插话（直接 push 到 messages，无需轮次）"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")
    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="会议已结束，无法插话")

    if meeting.status == "created":
        meeting.status = "running"

    msg = {
        "role": "user",
        "agentId": None,
        "agentName": "主持人",
        "content": req.content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    meeting.messages.append(msg)
    broadcast("meeting_message", {"meeting_id": meeting.id, "message": msg})

    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/finish", response_model=MeetingOut)
async def finish_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """结束会议（常驻，任何时候可调），生成纪要并归档到成果中心"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")
    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="会议已结束")
    return await _finish_meeting_internal(meeting, db)


async def _finish_meeting_internal(meeting: Meeting, db: Session) -> dict:
    """结束会议内部方法：生成纪要、存 Output、恢复 Agent 状态"""
    meeting.status = "finished"

    # 生成 Markdown 会议纪要（遍历扁平 messages）
    summary_lines = [
        f"# 会议纪要：{meeting.topic}",
        "",
        f"- 会议时间：{meeting.created_at.isoformat() if meeting.created_at else ''}",
        f"- 参会人员：{len(meeting.agent_ids or [])} 人",
        f"- 发言条数：{len(meeting.messages or [])} 条",
        "",
        "## 讨论内容",
        "",
    ]
    for m in (meeting.messages or []):
        speaker = m.get("agentName", "主持人")
        content = m.get("content", "")
        summary_lines.append(f"**{speaker}**：{content}")
        summary_lines.append("")

    summary_lines.extend(["", "## 决策建议", ""])
    for d in (meeting.decisions or []):
        summary_lines.append(f"- {d}")
    if not (meeting.decisions or []):
        summary_lines.append("- （暂无）")

    summary_lines.extend(["", "## 行动项", ""])
    for a in (meeting.actions or []):
        summary_lines.append(f"- {a}")
    if not (meeting.actions or []):
        summary_lines.append("- （暂无）")

    summary_text = "\n".join(summary_lines)
    meeting.summary = summary_text

    # 存到成果表
    output_id = f"output_{uuid.uuid4().hex[:8]}"
    output = Output(
        id=output_id,
        name=f"会议纪要 - {meeting.topic}",
        type="markdown",
        source="meeting",
        content=summary_text,
    )
    db.add(output)

    # 恢复 Agent 状态
    for aid in (meeting.agent_ids or []):
        agent = db.query(OfficeAgent).filter(
            (OfficeAgent.id == aid) | (OfficeAgent.platform_agent_id == aid)
        ).first()
        if agent:
            agent.status = "ONLINE"
            perf = agent.performance or {}
            perf["meetingCount"] = perf.get("meetingCount", 0) + 1
            agent.performance = perf

    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="meeting",
        title=f"会议结束：{meeting.topic}",
        description=f"共 {len(meeting.messages or [])} 条发言，纪要已生成",
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)

    broadcast("meeting_finished", {"meeting_id": meeting.id})

    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)
