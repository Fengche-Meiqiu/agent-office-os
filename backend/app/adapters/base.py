"""
Adapter 抽象基类 —— Agent 平台接入标准接口
所有 Agent 平台（Hermes/WorkBuddy/...）必须继承 BaseAdapter 并实现全部抽象方法。
Office OS 业务代码只面向 BaseAdapter 接口编程，不直接依赖任何具体平台。
新增平台只需：1) 继承 BaseAdapter 实现全部方法 2) 在 registry 的 init_adapters() 中注册一行
"""
from abc import ABC, abstractmethod
from typing import Any


class AdapterError(Exception):
    """Adapter 调用异常 —— 不再静默吞错，让上层能区分正常返回和降级返回"""

    def __init__(self, platform: str, method: str, detail: str):
        self.platform = platform
        self.method = method
        self.detail = detail
        super().__init__(f"[{platform}] {method} 失败: {detail}")


class BaseAdapter(ABC):
    """
    Agent 平台适配器基类（插接式接入标准）

    生命周期：
        应用启动时 init_adapters() 注册所有平台 Adapter
        业务代码通过 get_adapter(agent.platform) 获取实例
        调用 adapter.chat(...) / adapter.execute_task(...) 等方法
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台标识，如 'hermes' / 'workbuddy'，用于路由匹配"""

    # ===== Agent 发现与档案 =====

    @abstractmethod
    async def discover_agents(self) -> list[dict]:
        """
        发现平台上的所有 Agent
        返回标准格式：[{id, name, description, status, platform}]
        """

    @abstractmethod
    async def get_profile(self, agent_id: str) -> dict:
        """
        获取 Agent 详细档案
        返回：{id, name, role, description, platform, ...}
        """

    @abstractmethod
    async def get_skills(self, agent_id: str) -> list[dict]:
        """
        获取 Agent 的技能清单（结构化）
        返回：[{id, name, description, enabled}]
        如果平台只返回字符串，Adapter 内部做转换
        """

    @abstractmethod
    async def get_tools(self, agent_id: str) -> list[dict]:
        """
        获取 Agent 的工具清单
        返回：[{name, type}]
        """

    @abstractmethod
    async def get_memory(self, agent_id: str) -> dict:
        """
        获取 Agent 的长期记忆摘要
        返回：{summary: "..."}
        """

    # ===== 交互接口 =====

    @abstractmethod
    async def chat(self, agent_id: str, message: str, context: list | None = None) -> dict:
        """
        与 Agent 对话
        参数 context：历史消息列表，可选
        返回：{reply: "..."}
        失败时抛出 AdapterError，不返回降级文案（由上层处理）
        """

    @abstractmethod
    async def execute_task(
        self,
        agent_id: str,
        title: str,
        content: str,
        skills: list[str] | None = None,
    ) -> dict:
        """
        派发任务给 Agent 执行
        参数 skills：启用的技能 ID 列表，可选
        返回：{task_id: "..."}
        失败时抛出 AdapterError
        """

    @abstractmethod
    async def get_task(self, task_id: str) -> dict:
        """
        查询任务状态与结果
        返回：{status: "running"} 或 {status: "completed", result: "..."}
        """

    @abstractmethod
    async def meeting_respond(
        self, agent_id: str, meeting_id: str, topic: str, history: list
    ) -> dict:
        """
        让 Agent 在会议中发言
        参数 history：之前的发言记录列表
        返回：{opinion: "..."}
        失败时抛出 AdapterError
        """

    # ===== 管理接口 =====

    @abstractmethod
    async def refresh_agent(self, agent_id: str) -> dict:
        """
        强制重载 Agent 的最新配置（Profile/Skills/Tools 变更后调用）
        返回：{ok: True} 或抛出 AdapterError
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        检查平台连通性
        返回 True/False，不抛异常
        """
