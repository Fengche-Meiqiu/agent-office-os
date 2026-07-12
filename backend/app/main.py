"""
FastAPI 主入口
启动应用、注册路由、初始化数据库、注册 Adapter
"""
import sys
import asyncio

# 小白解释：Windows 上 Python 3.12 默认用 ProactorEventLoop，
# 在某些终端/沙箱里会报 "在一个非套接字上尝试了一个操作" 的错误。
# 这里把它改成 SelectorEventLoop，兼容性更好。
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

from app.config import settings
from app.database import init_db
from app.adapters import init_adapters
from app.adapters import get_adapter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时：建表 → 注册 Adapter → 按需加载种子数据
    """
    print("[启动] 正在初始化数据库...")
    init_db()

    print("[启动] 正在注册 Adapter...")
    init_adapters()

    print("[启动] 仅使用 Hermes 实时 Agent，不加载演示数据")

    print(f"[启动] {settings.APP_NAME} 后端已就绪 → http://localhost:{settings.PORT}")
    yield
    print("[关闭] 应用已停止")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Agent 虚拟办公室管理系统后端 API",
    version="2.0.0",
    lifespan=lifespan,
)

# 配置 CORS 跨域（允许前端访问）
# 小白解释：allow_credentials=True 时不能用通配符 "*"，否则浏览器会拒绝带凭据的请求。
# 这里只保留具体来源列表，生产环境可通过环境变量扩展 CORS_ORIGINS。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 小白解释：CORS 中间件默认不会给某些异常响应（如 404）加跨域头，
# 导致前端收到 "Failed to fetch" 而不是真实错误码。
# 这里加一个 HTTPException 专用处理器，保留原始状态码；再加一个兜底处理器。
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
        content={"detail": f"服务器内部错误：{exc}"},
    )


# ===== 注册路由 =====
from app.api import (
    marketplace,
    office,
    chat,
    tasks,
    meetings,
    outputs,
    webhook,
    event_logs,
    skills,
    sse,
)

app.include_router(marketplace.router)
app.include_router(office.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(meetings.router)
app.include_router(outputs.router)
app.include_router(webhook.router)
app.include_router(event_logs.router)
app.include_router(skills.router)
app.include_router(sse.router)


# ===== 健康检查 =====
@app.get("/api/health", tags=["系统"])
async def health_check():
    """健康检查接口，确认后端是否正常运行"""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


@app.get("/api/health/full", tags=["系统"])
async def health_check_full():
    """完整健康检查，含 Adapter 连通性"""
    result = {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
    # 检查 Hermes 连通性
    hermes_adapter = get_adapter("hermes")
    if hermes_adapter:
        try:
            connected = await hermes_adapter.health_check()
            result["hermes_bridge"] = "connected" if connected else "disconnected"
        except Exception:
            result["hermes_bridge"] = "disconnected"
    else:
        result["hermes_bridge"] = "not_registered"
    return result


@app.get("/", tags=["系统"])
async def root():
    """根路径，返回欢迎信息"""
    return {"message": "Agent Office OS API", "docs": "/docs"}
