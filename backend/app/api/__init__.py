"""
API 路由聚合模块
把所有路由文件统一导入，方便 main.py 一次性注册
"""
from . import marketplace, office, chat, tasks, meetings, outputs, webhook, event_logs

# 暴露所有路由模块，main.py 可以遍历注册
__all__ = [
    "marketplace",
    "office",
    "chat",
    "tasks",
    "meetings",
    "outputs",
    "webhook",
    "event_logs",
]

