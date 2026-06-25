"""
启动脚本
用 python run.py 启动后端服务
"""
import sys
import types

# ===== Windows 兼容性修复 =====
# 某些 Windows 环境（杀毒软件干扰）会导致 _overlapped 模块损坏
# 这里用空模块替代它，并使用 SelectorEventLoop（不依赖 _overlapped）
if sys.platform == 'win32':
    sys.modules['_overlapped'] = types.ModuleType('_overlapped')
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        loop="asyncio",
    )
