import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.adapters.hermes import hermes_adapter
from app.api.tasks import create_and_dispatch_task, task_to_out
from app.database import get_db
from app.models import ChatMessage, OfficeAgent
from app.schemas import ChatMessageOut, ChatSendRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _message_to_out(message: ChatMessage) -> dict:
    return {
        "id": message.id,
        "agentId": message.agent_id,
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp.isoformat() if message.timestamp else "",
    }


def _task_title(content: str) -> str:
    title = content.strip().removeprefix("/task").strip()
    return title[:60] or "Agent task"


@router.get("/{agent_id}/messages", response_model=list[ChatMessageOut])
async def get_chat_messages(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    messages = db.query(ChatMessage).filter(ChatMessage.agent_id == agent_id).order_by(ChatMessage.timestamp.asc()).all()
    return [_message_to_out(message) for message in messages]


@router.post("/{agent_id}/messages", response_model=ChatMessageOut)
async def send_chat_message(agent_id: str, req: ChatSendRequest, db: Session = Depends(get_db)):
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    now = datetime.utcnow()
    user_msg = ChatMessage(id=f"msg_{uuid.uuid4().hex[:8]}", agent_id=agent_id, role="user", content=req.content, timestamp=now)
    db.add(user_msg)

    if req.content.strip().lower().startswith("/task"):
        task_content = req.content.strip()[5:].strip()
        if not task_content:
            reply_content = "Please describe the task after /task."
        else:
            task = await create_and_dispatch_task(db, agent, _task_title(req.content), task_content)
            task_data = task_to_out(task)
            if task.output_id:
                reply_content = f"Task {task.id} is {task.status}. Result has been saved to Outputs."
            else:
                reply_content = f"Task {task.id} is {task.status}. You can monitor it in Task Center."
            task_json = json.dumps(task_data, ensure_ascii=False, indent=2)
            reply_content += f"\n\n```json\n{task_json}\n```"
    else:
        platform_id = agent.platform_agent_id or agent_id
        reply_data = await hermes_adapter.chat(platform_id, req.content)
        reply_content = reply_data.get("reply") or reply_data.get("content") or reply_data.get("message") or "Agent returned an empty response."

    agent_msg = ChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        role="agent",
        content=reply_content,
        timestamp=datetime.utcnow(),
    )
    db.add(agent_msg)
    agent.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(agent_msg)
    return _message_to_out(agent_msg)