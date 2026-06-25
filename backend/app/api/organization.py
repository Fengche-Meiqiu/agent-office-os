"""
组织架构路由
按部门分组展示办公室 Agent
相当于公司的"组织架构图"
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import defaultdict

from app.database import get_db
from app.models import OfficeAgent

# 创建路由器
router = APIRouter(prefix="/api/organization", tags=["组织架构"])


@router.get("")
async def get_organization(db: Session = Depends(get_db)):
    """
    获取按部门分组的 Agent 列表
    小白解释：把员工按部门归类，前端可以画成组织架构图
    返回格式：{ "技术部": [agent1, agent2], "市场部": [agent3] }
    """
    # 查所有办公室 Agent
    agents = db.query(OfficeAgent).all()

    # 按部门分组
    departments = defaultdict(list)
    for agent in agents:
        dept = agent.department or "未分配"
        departments[dept].append({
            "id": agent.id,
            "name": agent.name,
            "avatar": agent.avatar,
            "title": agent.title,
            "platform": agent.platform,
            "status": agent.status,
            "department": agent.department,
            "managerId": agent.manager_id,
            "hiredAt": agent.hired_at.isoformat() if agent.hired_at else None,
        })

    # 转成普通 dict 返回
    return dict(departments)
