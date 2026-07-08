import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.hermes import hermes_adapter
from app.database import get_db
from app.models import EventLog, Meeting, OfficeAgent, Output
from app.schemas import MeetingCreateRequest, MeetingMessageRequest, MeetingOut

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

MAX_ROUNDS = 4


def meeting_to_out(meeting: Meeting) -> dict:
    return {
        "id": meeting.id,
        "topic": meeting.topic,
        "agentIds": meeting.agent_ids or [],
        "status": meeting.status,
        "rounds": meeting.rounds or [],
        "summary": meeting.summary,
        "decisions": meeting.decisions or [],
        "actions": meeting.actions or [],
        "createdAt": meeting.created_at.isoformat() if meeting.created_at else None,
    }


def build_history(rounds: list) -> list[dict]:
    history: list[dict] = []
    for round_item in rounds or []:
        for message in round_item.get("messages", []):
            history.append({
                "role": message.get("role", "agent"),
                "content": message.get("content", ""),
                "agentName": message.get("agentName", ""),
            })
    return history


@router.get("", response_model=list[MeetingOut])
async def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [meeting_to_out(meeting) for meeting in meetings]


@router.post("", response_model=MeetingOut)
async def create_meeting(req: MeetingCreateRequest, db: Session = Depends(get_db)):
    for agent_id in req.agentIds:
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    meeting = Meeting(
        id=f"meeting_{uuid.uuid4().hex[:8]}",
        topic=req.topic,
        agent_ids=req.agentIds,
        status="created",
        rounds=[],
        decisions=[],
        actions=[],
    )
    db.add(meeting)

    for agent_id in req.agentIds:
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
        if agent:
            agent.status = "MEETING"

    db.add(EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="meeting",
        title=f"Meeting created: {req.topic}",
        description=f"Participants: {len(req.agentIds)}",
        timestamp=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/next-round", response_model=MeetingOut)
async def next_round(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="Meeting is already finished")

    rounds = meeting.rounds or []
    round_num = len(rounds) + 1
    if round_num > MAX_ROUNDS:
        return await finish_meeting_internal(meeting, db)

    history = build_history(rounds)
    messages = []
    for agent_id in meeting.agent_ids or []:
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
        if not agent:
            continue

        platform_id = agent.platform_agent_id or agent_id
        result = await hermes_adapter.meeting_respond(platform_id, meeting.id, meeting.topic, history)
        opinion = result.get("opinion") or result.get("content") or f"{agent.name} has no response right now."

        message = {
            "role": "agent",
            "agentId": agent_id,
            "agentName": agent.name,
            "content": opinion,
            "timestamp": datetime.utcnow().isoformat(),
        }
        messages.append(message)
        history.append({"role": "agent", "content": opinion, "agentName": agent.name})

    rounds.append({"round": round_num, "name": f"Round {round_num}", "messages": messages})
    meeting.rounds = rounds
    meeting.status = "running"
    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/messages", response_model=MeetingOut)
async def add_meeting_message(meeting_id: str, req: MeetingMessageRequest, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="Meeting is already finished")

    rounds = meeting.rounds or []
    if not rounds:
        rounds.append({"round": 1, "name": "Round 1", "messages": []})
        meeting.status = "running"

    rounds[-1]["messages"].append({
        "role": "user",
        "agentId": None,
        "agentName": "User",
        "content": req.content,
        "timestamp": datetime.utcnow().isoformat(),
    })
    meeting.rounds = rounds
    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/finish", response_model=MeetingOut)
async def finish_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return await finish_meeting_internal(meeting, db)


async def finish_meeting_internal(meeting: Meeting, db: Session) -> dict:
    meeting.status = "finished"

    summary_lines = [
        f"# Meeting Notes: {meeting.topic}",
        "",
        f"- Created at: {meeting.created_at.isoformat() if meeting.created_at else ''}",
        f"- Participants: {len(meeting.agent_ids or [])}",
        f"- Rounds: {len(meeting.rounds or [])}",
        "",
        "## Discussion",
        "",
    ]

    for round_item in meeting.rounds or []:
        round_num = round_item.get("round", 0)
        round_name = round_item.get("name") or f"Round {round_num}"
        summary_lines.extend([f"### {round_name}", ""])
        for message in round_item.get("messages", []):
            speaker = message.get("agentName") or "User"
            content = message.get("content") or ""
            summary_lines.extend([f"**{speaker}**: {content}", ""])

    summary_lines.extend(["## Decisions", ""])
    decisions = meeting.decisions or []
    summary_lines.extend([f"- {item}" for item in decisions] or ["- None yet"])
    summary_lines.extend(["", "## Action Items", ""])
    actions = meeting.actions or []
    summary_lines.extend([f"- {item}" for item in actions] or ["- None yet"])
    summary_lines.append("")

    summary_text = "\n".join(summary_lines)
    meeting.summary = summary_text

    output = Output(
        id=f"output_{uuid.uuid4().hex[:8]}",
        name=f"Meeting notes - {meeting.topic}",
        type="markdown",
        source="meeting",
        content=summary_text,
        created_at=datetime.utcnow(),
    )
    db.add(output)

    for agent_id in meeting.agent_ids or []:
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
        if agent:
            agent.status = "ONLINE"
            performance = agent.performance or {"totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0}
            performance["meetingCount"] = int(performance.get("meetingCount", 0)) + 1
            agent.performance = performance

    db.add(EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="meeting",
        title=f"Meeting finished: {meeting.topic}",
        description=f"Rounds: {len(meeting.rounds or [])}; output: {output.id}",
        timestamp=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(meeting)
    return meeting_to_out(meeting)
