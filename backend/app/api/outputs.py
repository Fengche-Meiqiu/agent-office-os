"""
成果路由
查询任务和会议产出的成果文件
相当于公司的"成果档案室"
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Output
from app.schemas import OutputOut

# 创建路由器
router = APIRouter(prefix="/api/outputs", tags=["成果管理"])


def output_to_out(output: Output) -> dict:
    """
    把数据库模型转成响应字典
    小白解释：数据库字段 created_at 转成前端要的 createdAt（驼峰风格）
    """
    return {
        "id": output.id,
        "name": output.name,
        "type": output.type,
        "source": output.source,
        "content": output.content,
        "url": output.url,
        "createdAt": output.created_at.isoformat() if output.created_at else None,
    }


@router.get("", response_model=list[OutputOut])
async def list_outputs(db: Session = Depends(get_db)):
    """
    获取所有成果列表
    小白解释：查看办公室产出的所有文件和报告
    """
    outputs = db.query(Output).order_by(Output.created_at.desc()).all()
    return [output_to_out(o) for o in outputs]


@router.get("/{output_id}", response_model=OutputOut)
async def get_output(output_id: str, db: Session = Depends(get_db)):
    """
    获取单个成果详情
    小白解释：查看某个具体文件的内容
    """
    output = db.query(Output).filter(Output.id == output_id).first()
    if not output:
        raise HTTPException(status_code=404, detail="找不到该成果")
    return output_to_out(output)
