"""
数据库连接与会话管理
使用 SQLAlchemy 2.0 风格，SQLite 文件型数据库
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


# 创建数据库引擎
# check_same_thread=False：允许多线程访问（FastAPI 异步需要）
# connect_args 设置 SQLite 特有参数
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,  # 调试模式打印 SQL
)

# 会话工厂：每个请求创建一个独立会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有数据库模型的基类"""
    pass


def get_db():
    """
    依赖注入函数：为每个请求提供数据库会话
    用法：在路由参数中加 db: Session = Depends(get_db)
    请求结束后自动关闭会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations():
    """
    执行轻量级数据库迁移
    小白解释：这里放一些简单的 ALTER TABLE，让老数据库能兼容新代码。
    生产环境建议用 Alembic 等专业迁移工具。
    """
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    with engine.connect() as conn:
        # 清理旧版本固定 ID 的演示数据；不会触碰 Hermes 同步生成的真实记录。
        demo_ids = {
            "agent_marketplace": [f"market_{i:03d}" for i in range(1, 9)],
            "office_agent": [f"office_{i:03d}" for i in range(1, 5)],
            "task": [f"task_{i:03d}" for i in range(1, 7)],
            "meeting": ["meeting_001"],
            "output": [f"output_{i:03d}" for i in range(1, 9)],
            "chat_history": [f"chat_{i:03d}" for i in range(1, 13)],
            "event_log": [f"event_{i:03d}" for i in range(1, 11)],
        }
        for table, ids in demo_ids.items():
            params = {f"id_{i}": value for i, value in enumerate(ids)}
            placeholders = ", ".join(f":id_{i}" for i in range(len(ids)))
            conn.execute(text(f"DELETE FROM {table} WHERE id IN ({placeholders})"), params)
        conn.execute(text("DELETE FROM agent_mapping WHERE office_agent_id LIKE 'office_00_'"))
        conn.commit()

        # V2.1 迁移：给 chat_history 表添加 suggest_task 字段
        try:
            conn.execute(text(
                "ALTER TABLE chat_history ADD COLUMN suggest_task BOOLEAN DEFAULT 0"
            ))
            conn.commit()
            print("[迁移] chat_history.suggest_task 字段已添加")
        except OperationalError as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("[迁移] chat_history.suggest_task 字段已存在，跳过")
            else:
                raise


def init_db():
    """初始化数据库：创建所有表 + 执行轻量迁移"""
    # 导入模型模块，确保所有表类被注册到 Base.metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_migrations()

