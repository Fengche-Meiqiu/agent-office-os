"""
聊天路由（V2 重写）
核心变更：
1. 使用 get_adapter_or_raise(agent.platform) 路由，不硬编码 hermes_adapter
2. 调用 resolve_platform_id 统一身份映射
3. chat() 传入 context（历史对话）
4. AdapterError 不再静默降级，直接抛 502
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OfficeAgent, ChatMessage, AgentMapping
from app.schemas import ChatMessageOut, ChatSendRequest
from app.adapters import get_adapter_or_raise
from app.adapters.base import AdapterError
from app.api.sse import broadcast

# 创建路由器
router = APIRouter(prefix="/api/chat", tags=["聊天"])


def resolve_platform_id(agent: OfficeAgent, db: Session) -> str:
    """
    统一身份映射：查 AgentMapping 表获取真实 platform_agent_id
    和 meetings.py 中同一个函数，确保调用 Adapter 前拿到正确的平台 ID
    """
    mapping = db.query(AgentMapping).filter(
        AgentMapping.office_agent_id == agent.id
    ).first()
    if mapping and mapping.platform_agent_id:
        return mapping.platform_agent_id
    if agent.platform_agent_id:
        return agent.platform_agent_id
    return agent.id


@router.get("/{agent_id}/messages", response_model=list[ChatMessageOut])
async def get_chat_messages(agent_id: str, db: Session = Depends(get_db)):
    """
    获取某个 Agent 的聊天记录
    小白解释：查看你和某个 Agent 之前聊过什么
    """
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    messages = db.query(ChatMessage).filter(
        ChatMessage.agent_id == agent_id
    ).order_by(ChatMessage.timestamp.asc()).all()

    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "agentId": m.agent_id,
            "role": m.role,
            "content": m.content,
            "suggestTask": bool(getattr(m, 'suggest_task', False)),
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
    V2：chat() 传入历史 context，让 Agent 能联系上下文回答
    """
    # 第一步：检查 Agent 是否存在
    agent = db.query(OfficeAgent).filter(OfficeAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="找不到该 Agent")

    # 第二步：存用户消息
    user_msg = ChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        role="user",
        content=req.content,
        timestamp=datetime.utcnow(),
    )
    db.add(user_msg)

    # 第三步：取最近 20 条历史作为 context
    history = db.query(ChatMessage).filter(
        ChatMessage.agent_id == agent_id
    ).order_by(ChatMessage.timestamp.desc()).limit(20).all()
    history.reverse()  # 从旧到新
    context = [{"role": m.role, "content": m.content} for m in history]

    # 第四步：调用 Adapter 让 Agent 回复
    platform_id = resolve_platform_id(agent, db)
    try:
        adapter = get_adapter_or_raise(agent.platform)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    try:
        reply_data = await adapter.chat(platform_id, req.content, context=context)
        reply_content = reply_data.get("reply", "")
        # 小白解释：Hermes 返回 suggest_task=true 时，表示建议用户改用 /task 异步任务模式
        suggest_task = bool(reply_data.get("suggest_task", False))
    except AdapterError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Agent 回复失败（{agent.platform}）：{e.detail}",
        )

    # 第五步：存 Agent 回复
    agent_msg = ChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        role="agent",
        content=reply_content,
        suggest_task=suggest_task,
        timestamp=datetime.utcnow(),
    )
    db.add(agent_msg)

    agent.last_active_at = datetime.utcnow()

    db.commit()

    # SSE 推送聊天消息
    broadcast("chat_message", {
        "agentId": agent_id,
        "message": {
            "id": agent_msg.id,
            "agentId": agent_id,
            "role": "agent",
            "content": reply_content,
            "timestamp": agent_msg.timestamp.isoformat() if agent_msg.timestamp else "",
        },
    })

    return {
        "id": agent_msg.id,
        "agentId": agent_id,
        "role": "agent",
        "content": reply_content,
        "suggestTask": suggest_task,
        "timestamp": agent_msg.timestamp.isoformat() if agent_msg.timestamp else "",
    }
