"""
会议路由
管理多 Agent 会议的创建、讨论、结束
相当于公司的"会议室预订与会议记录系统"
"""
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
from app.adapters.hermes import hermes_adapter

# 创建路由器
router = APIRouter(prefix="/api/meetings", tags=["会议管理"])

# 最大会议轮次，超过这个数自动结束
MAX_ROUNDS = 4


def meeting_to_out(meeting: Meeting) -> dict:
    """
    把数据库模型转成响应字典
    小白解释：数据库字段是下划线风格，前端要驼峰风格，这里转换一下
    """
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


def build_history(rounds: list) -> list:
    """
    把已有的会议轮次整理成 Hermes 需要的历史记录格式
    小白解释：让 Agent 发言前，先把之前大家说过的话整理好告诉他，这样他才能接着聊
    """
    history = []
    for r in rounds:
        for m in r.get("messages", []):
            history.append({
                "role": m.get("role", "agent"),
                "content": m.get("content", ""),
                "agentName": m.get("agentName", ""),
            })
    return history


@router.get("", response_model=list[MeetingOut])
async def list_meetings(db: Session = Depends(get_db)):
    """
    获取所有会议列表
    小白解释：查看公司开过哪些会
    """
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [meeting_to_out(m) for m in meetings]


@router.post("", response_model=MeetingOut)
async def create_meeting(req: MeetingCreateRequest, db: Session = Depends(get_db)):
    """
    创建新会议
    小白解释：预订一个会议室，选定参会人员，定好议题
    """
    # 检查参会 Agent 是否都存在
    for aid in req.agentIds:
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == aid).first()
        if not agent:
            raise HTTPException(status_code=404, detail=f"参会 Agent 不存在：{aid}")

    # 创建会议记录
    meeting_id = f"meeting_{uuid.uuid4().hex[:8]}"
    meeting = Meeting(
        id=meeting_id,
        topic=req.topic,
        agent_ids=req.agentIds,
        status="created",
        rounds=[],
    )
    db.add(meeting)

    # 把参会 Agent 状态改成开会中
    for aid in req.agentIds:
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == aid).first()
        if agent:
            agent.status = "MEETING"

    # 写一条事件日志
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
    """
    获取会议详情
    小白解释：查看某个会议的详细情况，包括各轮讨论内容
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")
    return meeting_to_out(meeting)


@router.post("/{meeting_id}/next-round", response_model=MeetingOut)
async def next_round(meeting_id: str, db: Session = Depends(get_db)):
    """
    进入下一轮讨论
    小白解释：让每个参会 Agent 轮流发言一轮。如果已经开了 4 轮以上，自动结束会议
    """
    # 第一步：找到会议
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")

    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="会议已结束，无法继续讨论")

    # 第二步：计算当前轮次
    current_rounds = meeting.rounds or []
    next_round_num = len(current_rounds) + 1

    # 第三步：如果超过最大轮次，自动结束会议
    if next_round_num > MAX_ROUNDS:
        # 自动结束会议并生成纪要
        return await finish_meeting_internal(meeting, db)

    # 第四步：让每个参会 Agent 发言
    # 先整理好之前的对话历史，告诉 Agent 之前大家说了啥
    history = build_history(current_rounds)

    new_messages = []
    for aid in meeting.agent_ids:
        # 查 Agent 信息
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == aid).first()
        if not agent:
            continue

        # 调用 Hermes 让 Agent 发言
        platform_id = agent.platform_agent_id or aid
        result = await hermes_adapter.meeting_respond(
            platform_id, meeting_id, meeting.topic, history
        )
        opinion = result.get("opinion", "（暂无意见）")

        # 记录这条发言
        msg = {
            "role": "agent",
            "agentId": aid,
            "agentName": agent.name,
            "content": opinion,
            "timestamp": datetime.utcnow().isoformat(),
        }
        new_messages.append(msg)

        # 同时更新历史，让下一个 Agent 能看到这条发言
        history.append({
            "role": "agent",
            "content": opinion,
            "agentName": agent.name,
        })

    # 第五步：把新轮次加到会议记录里
    new_round = {
        "round": next_round_num,
        "name": f"第 {next_round_num} 轮",
        "messages": new_messages,
    }
    current_rounds.append(new_round)
    meeting.rounds = current_rounds
    meeting.status = "running"

    db.commit()
    db.refresh(meeting)

    return meeting_to_out(meeting)


@router.post("/{meeting_id}/messages", response_model=MeetingOut)
async def add_meeting_message(
    meeting_id: str,
    req: MeetingMessageRequest,
    db: Session = Depends(get_db),
):
    """
    主持人插话
    小白解释：会议进行中，主持人（用户）想说一句话，插到当前讨论里
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")

    if meeting.status == "finished":
        raise HTTPException(status_code=400, detail="会议已结束，无法插话")

    current_rounds = meeting.rounds or []

    # 如果还没有任何轮次，先创建一个空轮次
    if not current_rounds:
        current_rounds.append({
            "round": 1,
            "name": "第 1 轮",
            "messages": [],
        })
        meeting.status = "running"

    # 把主持人的话加到最后一轮
    last_round = current_rounds[-1]
    last_round["messages"].append({
        "role": "user",
        "agentId": None,
        "agentName": "主持人",
        "content": req.content,
        "timestamp": datetime.utcnow().isoformat(),
    })

    meeting.rounds = current_rounds

    db.commit()
    db.refresh(meeting)

    return meeting_to_out(meeting)


@router.post("/{meeting_id}/finish", response_model=MeetingOut)
async def finish_meeting(meeting_id: str, db: Session = Depends(get_db)):
    """
    结束会议并生成会议纪要
    小白解释：会议开完了，生成一份 Markdown 格式的纪要存档
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="找不到该会议")

    return await finish_meeting_internal(meeting, db)


async def finish_meeting_internal(meeting: Meeting, db: Session) -> dict:
    """
    结束会议的内部方法（供 next-round 自动结束和手动结束共用）
    小白解释：这是真正干活的函数，把会议标记为结束，生成纪要，存到成果库
    """
    # 第一步：标记会议结束
    meeting.status = "finished"

    # 第二步：生成 Markdown 格式会议纪要
    summary_lines = [
        f"# 会议纪要：{meeting.topic}",
        "",
        f"- 会议时间：{meeting.created_at.isoformat() if meeting.created_at else ''}",
        f"- 参会人员：{len(meeting.agent_ids or [])} 人",
        f"- 讨论轮次：{len(meeting.rounds or [])} 轮",
        "",
        "## 讨论内容",
        "",
    ]

    for r in (meeting.rounds or []):
        summary_lines.append(f"### {r.get('name', f'第 {r.get('round', 0)} 轮')}")
        summary_lines.append("")
        for m in r.get("messages", []):
            speaker = m.get("agentName", "主持人")
            content = m.get("content", "")
            summary_lines.append(f"**{speaker}**：{content}")
            summary_lines.append("")
        summary_lines.append("")

    summary_lines.append("## 决策建议")
    for d in (meeting.decisions or []):
        summary_lines.append(f"- {d}")
    if not (meeting.decisions or []):
        summary_lines.append("- （暂无）")
    summary_lines.append("")

    summary_lines.append("## 行动项")
    for a in (meeting.actions or []):
        summary_lines.append(f"- {a}")
    if not (meeting.actions or []):
        summary_lines.append("- （暂无）")
    summary_lines.append("")

    summary_text = "\n".join(summary_lines)
    meeting.summary = summary_text

    # 第三步：把纪要存到成果表
    output_id = f"output_{uuid.uuid4().hex[:8]}"
    output = Output(
        id=output_id,
        name=f"会议纪要 - {meeting.topic}",
        type="markdown",
        source="meeting",
        content=summary_text,
    )
    db.add(output)

    # 第四步：把参会 Agent 状态改回在线
    for aid in (meeting.agent_ids or []):
        agent = db.query(OfficeAgent).filter(OfficeAgent.id == aid).first()
        if agent:
            agent.status = "ONLINE"
            # 更新参会次数
            perf = agent.performance or {
                "totalTasks": 0, "successTasks": 0, "failedTasks": 0, "meetingCount": 0
            }
            perf["meetingCount"] = perf.get("meetingCount", 0) + 1
            agent.performance = perf

    # 第五步：写一条事件日志
    event_log = EventLog(
        id=f"event_{uuid.uuid4().hex[:8]}",
        type="meeting",
        title=f"会议结束：{meeting.topic}",
        description=f"共 {len(meeting.rounds or [])} 轮讨论，纪要已生成",
        timestamp=datetime.utcnow(),
    )
    db.add(event_log)

    db.commit()
    db.refresh(meeting)

    return meeting_to_out(meeting)
