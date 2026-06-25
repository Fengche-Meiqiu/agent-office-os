"""
事件日志路由
查询和清空系统事件日志
相当于公司的"公告栏"，记录所有重要事件
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EventLog
from app.schemas import EventLogOut

# 创建路由器
router = APIRouter(prefix="/api/event-logs", tags=["事件日志"])


@router.get("", response_model=list[EventLogOut])
async def list_event_logs(db: Session = Depends(get_db)):
    """
    获取所有事件日志
    小白解释：查看系统里发生过哪些事，按时间倒序排列（最新的在最前面）
    """
    logs = db.query(EventLog).order_by(EventLog.timestamp.desc()).all()
    # EventLogOut 字段与模型一致，但 timestamp 需要转成字符串
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "type": log.type,
            "title": log.title,
            "description": log.description,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
        })
    return result


@router.delete("")
async def clear_event_logs(db: Session = Depends(get_db)):
    """
    清空所有事件日志
    小白解释：把公告栏上的旧消息全部清掉
    """
    db.query(EventLog).delete()
    db.commit()
    return {"message": "事件日志已清空"}
