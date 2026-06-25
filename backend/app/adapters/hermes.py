"""
Hermes Adapter 适配层
按照《Hermes Adapter 技术规范》实现 9 个标准接口
Office OS 通过 Adapter 调用 Hermes，不直接连接
"""
import httpx
from typing import Optional
from app.config import settings


class HermesAdapter:
    """
    Hermes 平台适配器
    负责与 Hermes API 通信，实现 Agent 发现、信息同步、聊天、任务、会议等功能
    """

    def __init__(self, base_url: str = None):
        # Hermes API 地址，默认从配置读取
        self.base_url = base_url or settings.HERMES_URL
        # 使用 httpx 异步客户端，超时 30 秒
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def discover_agents(self) -> list[dict]:
        """
        发现 Hermes 中的全部 Agent
        对应文档第 4 节：Agent 发现
        返回：[{id, name, description, status}]
        """
        try:
            resp = await self.client.get("/api/agents")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            # Hermes 不可用时返回空列表，不阻断启动
            print(f"[HermesAdapter] discover_agents 失败: {e}")
            return []

    async def get_profile(self, agent_id: str) -> dict:
        """
        获取 Agent 详细信息
        对应文档第 5 节：Agent Profile
        """
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] get_profile 失败: {e}")
            return {}

    async def get_skills(self, agent_id: str) -> list[str]:
        """
        获取 Agent 技能列表
        对应文档第 6 节：Skill 同步
        """
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/skills")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] get_skills 失败: {e}")
            return []

    async def get_tools(self, agent_id: str) -> list[dict]:
        """
        获取 Agent 工具能力
        对应文档第 7 节：Tool 同步
        返回：[{name, type}]
        """
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/tools")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] get_tools 失败: {e}")
            return []

    async def get_memory(self, agent_id: str) -> dict:
        """
        获取 Agent 记忆摘要
        对应文档第 8 节：Memory 同步
        V1 仅展示摘要，不支持编辑
        """
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/memory")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] get_memory 失败: {e}")
            return {"summary": ""}

    async def chat(self, agent_id: str, message: str) -> dict:
        """
        与 Agent 聊天
        对应文档第 9 节：Chat
        返回：{reply: "..."}
        """
        try:
            resp = await self.client.post(
                f"/api/agents/{agent_id}/chat",
                json={"message": message}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] chat 失败: {e}")
            return {"reply": f"抱歉，暂时无法连接到 Agent（{e}）"}

    async def execute_task(self, agent_id: str, title: str, content: str) -> dict:
        """
        派发任务给 Agent 执行
        对应文档第 10 节：Task
        返回：{task_id: "..."}
        """
        try:
            resp = await self.client.post(
                "/api/tasks",
                json={"agent_id": agent_id, "title": title, "content": content}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] execute_task 失败: {e}")
            return {"task_id": "", "error": str(e)}

    async def get_task(self, task_id: str) -> dict:
        """
        查询任务状态与结果
        对应文档第 11 节：Task Query
        返回：{status: "running"} 或 {status: "completed", result: "..."}
        """
        try:
            resp = await self.client.get(f"/api/tasks/{task_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] get_task 失败: {e}")
            return {"status": "unknown"}

    async def meeting_respond(self, agent_id: str, meeting_id: str, topic: str, history: list) -> dict:
        """
        让 Agent 在会议中发言
        对应文档第 12 节：Meeting Support
        返回：{opinion: "..."}
        """
        try:
            resp = await self.client.post(
                "/api/meetings/respond",
                json={
                    "agent_id": agent_id,
                    "meeting_id": meeting_id,
                    "topic": topic,
                    "history": history,
                }
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[HermesAdapter] meeting_respond 失败: {e}")
            return {"opinion": f"（{agent_id} 暂时无法响应）"}


# 全局 Adapter 实例
hermes_adapter = HermesAdapter()
