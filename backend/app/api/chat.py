"""
聊天路由
处理用户与 Agent 的对话
相当于公司的"内部沟通工具"
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OfficeAgent, ChatMessage
from app.schemas import ChatMessageOut, ChatSendRequest
from app.adapters.hermes import hermes_adapter

# 创建路由器
router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.get("/{agent_id}/messages", response_model=list[ChatMessageOut])
async def get_chat_messages(agent_id: str, db: Session = Depends(get_db)):
    """
    获取某个 Agent 的聊天记录
    小白解释：查看你和某个 Agent 之前聊过什么
    """
    # 先检查 Agent 是否存在
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    # 查询所有聊天记录，按时间正序排列（从旧到新）
    messages = db.query(ChatMessage).filter(
        ChatMessage.agent_id == agent_id
    ).order_by(ChatMessage.timestamp.asc()).all()

    # 转换字段名（驼峰风格）
    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "agentId": m.agent_id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat() if m.timestamp else "",
        })
    return result


@router.post("/{agent_id}/messages", response_model=ChatMessageOut)
async def send_chat_message(
    agent_id: str,
    req: ChatSendRequest,
    db: Session = Depends(get_db),
):
    """
    给 Agent 发消息并获取回复
    小白解释：你发一句话给 Agent，Agent 回你一句话，两边的话都存到数据库
    """
    # 第一步：检查 Agent 是否存在
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    # 第二步：把用户的消息存到数据库
    user_msg = ChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        role="user",
        content=req.content,
        timestamp=datetime.utcnow(),
    )
    db.add(user_msg)

    # 第三步：调用 Hermes 让 Agent 回复
    # platform_agent_id 是 Agent 在源平台的 ID，Hermes 需要用它来定位 Agent
    platform_id = agent.platform_agent_id or agent_id
    reply_data = await hermes_adapter.chat(platform_id, req.content)
    reply_content = reply_data.get("reply", "（Agent 暂时无法回复）")

    # 第四步：把 Agent 的回复存到数据库
    agent_msg = ChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        role="agent",
        content=reply_content,
        timestamp=datetime.utcnow(),
    )
    db.add(agent_msg)

    # 第五步：更新 Agent 的最后活跃时间
    agent.last_active_at = datetime.utcnow()

    db.commit()

    # 返回 Agent 的回复消息
    return {
        "id": agent_msg.id,
        "agentId": agent_id,
        "role": "agent",
        "content": reply_content,
        "timestamp": agent_msg.timestamp.isoformat() if agent_msg.timestamp else "",
    }
