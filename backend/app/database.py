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


def init_db():
    """初始化数据库：创建所有表"""
    # 导入模型模块，确保所有表类被注册到 Base.metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
