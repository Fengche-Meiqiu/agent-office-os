"""
FastAPI 主入口
启动应用、注册路由、初始化数据库与种子数据
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.seed import init_seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时：初始化数据库表 + 写入种子数据
    关闭时：清理资源
    """
    # 启动时执行
    print("[启动] 正在初始化数据库...")
    init_db()
    print("[启动] 正在检查种子数据...")
    init_seed_data()
    print(f"[启动] {settings.APP_NAME} 后端已就绪 → http://localhost:{settings.PORT}")
    yield
    # 关闭时执行（暂无需要清理的资源）
    print("[关闭] 应用已停止")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Agent 虚拟办公室管理系统后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS 跨域（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 注册路由 =====
from app.api import marketplace, office, chat, tasks, meetings, outputs, organization, webhook, event_logs

app.include_router(marketplace.router)
app.include_router(office.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(meetings.router)
app.include_router(outputs.router)
app.include_router(organization.router)
app.include_router(webhook.router)
app.include_router(event_logs.router)


# ===== 健康检查 =====
@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口，用于确认后端是否正常运行"""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@app.get("/", tags=["系统"])
async def root():
    """根路径，返回欢迎信息"""
    return {"message": "Agent Office OS API", "docs": "/docs"}
