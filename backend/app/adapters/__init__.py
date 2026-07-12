"""
适配器包初始化
对外暴露注册中心和基类，不直接暴露具体平台 Adapter 单例
"""
from app.adapters.base import BaseAdapter, AdapterError
from app.adapters.registry import (
    get_adapter,
    get_adapter_or_raise,
    register_adapter,
    list_platforms,
    init_adapters,
)

__all__ = [
    "BaseAdapter",
    "AdapterError",
    "get_adapter",
    "get_adapter_or_raise",
    "register_adapter",
    "list_platforms",
    "init_adapters",
]
