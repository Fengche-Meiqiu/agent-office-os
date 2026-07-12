"""
Adapter 注册中心 —— 插接式路由
- 平台 Adapter 在此注册
- 业务代码通过 get_adapter(platform) 获取对应实例
- 新增平台只需 register_adapter(MyAdapter())，不改任何业务代码

使用方式：
    from app.adapters.registry import get_adapter
    adapter = get_adapter(agent.platform)
    if adapter is None:
        raise ValueError(f"不支持的平台: {agent.platform}")
    result = await adapter.chat(platform_id, message)
"""
from app.adapters.base import BaseAdapter

# 全局注册表：platform_name -> Adapter 实例
_registry: dict[str, BaseAdapter] = {}


def register_adapter(adapter: BaseAdapter) -> None:
    """注册一个平台 Adapter（幂等，重复注册会覆盖旧实例）"""
    # 小白解释：平台名统一用小写存，避免 "Hermes" / "hermes" 混用导致找不到 Adapter
    key = adapter.platform_name.lower()
    _registry[key] = adapter
    print(f"[Adapter注册] {key} 已注册")


def get_adapter(platform: str) -> BaseAdapter | None:
    """根据平台名获取 Adapter，找不到返回 None（大小写不敏感）"""
    return _registry.get(platform.lower())


def get_adapter_or_raise(platform: str) -> BaseAdapter:
    """根据平台名获取 Adapter，找不到抛出 ValueError（大小写不敏感）"""
    adapter = get_adapter(platform)
    if adapter is None:
        raise ValueError(
            f"不支持的平台: '{platform}'，已注册平台: {list(_registry.keys())}"
        )
    return adapter


def list_platforms() -> list[str]:
    """列出所有已注册平台"""
    return list(_registry.keys())


def init_adapters() -> None:
    """
    应用启动时初始化所有 Adapter
    新增平台只需在这里加一行 register_adapter(YourAdapter())
    """
    from app.adapters.hermes import HermesAdapter

    register_adapter(HermesAdapter())
    # 未来接入其他平台：
    # from app.adapters.workbuddy import WorkBuddyAdapter
    # register_adapter(WorkBuddyAdapter())
