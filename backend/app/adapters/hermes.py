"""
Hermes Adapter —— Hermes 平台的 BaseAdapter 实现
按照《Hermes Adapter 技术规范》实现标准接口
Office OS 通过 AdapterRegistry 获取本实例，不直接导入
"""
import httpx
from typing import Optional
from app.adapters.base import BaseAdapter, AdapterError
from app.config import settings


class HermesAdapter(BaseAdapter):
    """
    Hermes 平台适配器
    负责与 Hermes API 通信，实现 Agent 发现、信息同步、聊天、任务、会议等功能

    与上一版的区别：
    1. 继承 BaseAdapter，实现标准接口
    2. 不再静默吞错——交互接口(chat/execute_task/meeting_respond)失败抛 AdapterError
    3. get_skills 返回结构化 list[dict] 而非 list[str]
    4. 新增 refresh_agent、health_check 方法
    5. 超时从 30s 提升到 120s(交互)/300s(任务)
    """

    def __init__(self, base_url: str = None):
        self._base_url = base_url or settings.HERMES_URL
        self.client = httpx.AsyncClient(
            base_url=self._base_url, timeout=httpx.Timeout(120.0, connect=10.0)
        )

    @property
    def platform_name(self) -> str:
        return "hermes"

    # ===== Agent 发现与档案 =====

    async def discover_agents(self) -> list[dict]:
        """发现 Hermes 中的全部 Agent，启动时调用，不抛异常"""
        try:
            resp = await self.client.get("/api/agents")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            # discover 在启动/同步时调用，失败返回空列表不阻断
            print(f"[HermesAdapter] discover_agents 失败: {e}")
            return []

    async def get_profile(self, agent_id: str) -> dict:
        """获取 Agent 详细信息"""
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise AdapterError("hermes", "get_profile", str(e))

    async def get_skills(self, agent_id: str) -> list[dict]:
        """
        获取 Agent 技能清单（结构化）
        Hermes 可能返回字符串列表，这里统一转换为 dict 格式
        返回：[{id, name, description, enabled}]
        """
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/skills")
            resp.raise_for_status()
            raw = resp.json()
            # Hermes 可能返回 ["skill_a", "skill_b"] 或 [{"id":..., "name":...}]
            result = []
            for item in raw:
                if isinstance(item, str):
                    result.append(
                        {"id": item, "name": item, "description": "", "enabled": True}
                    )
                elif isinstance(item, dict):
                    result.append(
                        {
                            "id": item.get("id", item.get("name", "")),
                            "name": item.get("name", item.get("id", "")),
                            "description": item.get("description", ""),
                            "enabled": item.get("enabled", True),
                        }
                    )
            return result
        except Exception as e:
            raise AdapterError("hermes", "get_skills", str(e))

    async def get_tools(self, agent_id: str) -> list[dict]:
        """获取 Agent 工具能力，返回 [{name, type}]"""
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/tools")
            resp.raise_for_status()
            raw = resp.json()
            result = []
            for item in raw:
                if isinstance(item, str):
                    result.append({"name": item, "type": "unknown"})
                elif isinstance(item, dict):
                    result.append(
                        {"name": item.get("name", ""), "type": item.get("type", "unknown")}
                    )
            return result
        except Exception as e:
            raise AdapterError("hermes", "get_tools", str(e))

    async def get_memory(self, agent_id: str) -> dict:
        """获取 Agent 记忆摘要，返回 {summary: "..."}"""
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/memory")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise AdapterError("hermes", "get_memory", str(e))

    # ===== 交互接口（失败抛 AdapterError，不返回降级文案）=====

    async def chat(
        self, agent_id: str, message: str, context: list | None = None
    ) -> dict:
        """
        与 Agent 聊天
        参数 context：历史消息列表，传给 Hermes 让 Agent 有上下文
        返回：{reply: "..."}
        """
        import traceback
        try:
            body = {"message": message}
            if context:
                body["context"] = context
            print(f"[HermesAdapter.chat] request POST /api/agents/{agent_id}/chat body={body}")
            # 小白解释：Hermes 团队确认 chat 接口简单对话需 8-12 秒，
            # 分析类请求需 60-120 秒，所以这里设置为 120 秒。
            resp = await self.client.post(
                f"/api/agents/{agent_id}/chat", json=body, timeout=120.0
            )
            print(f"[HermesAdapter.chat] response status={resp.status_code} body={resp.text[:500]}")
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as e:
            # 超时单独处理，给用户更明确的错误信息
            print(f"[HermesAdapter.chat] timeout: {e}")
            traceback.print_exc()
            raise AdapterError(
                "hermes", "chat",
                "请求 Hermes 聊天接口超时（120 秒无响应），请检查 Hermes 服务是否正常或 Agent 是否过于繁忙"
            )
        except Exception as e:
            print(f"[HermesAdapter.chat] error: {e}")
            traceback.print_exc()
            raise AdapterError("hermes", "chat", str(e))

    async def execute_task(
        self,
        agent_id: str,
        title: str,
        content: str,
        skills: list[str] | None = None,
    ) -> dict:
        """
        派发任务给 Agent 执行
        参数 skills：启用的技能 ID 列表（可选）
        返回：{task_id: "..."}

        小白解释：Hermes 的 POST /api/tasks 只认 {agent_id, content} 两个字段，
        这里按 Hermes 文档严格发送，避免多余字段导致校验失败。
        """
        import traceback
        try:
            body = {"agent_id": agent_id, "content": content or title}
            print(f"[HermesAdapter.execute_task] request POST /api/tasks body={body}")
            # 小白解释：Hermes 创建任务应该是秒回 task_id，设 60 秒超时防止死等。
            resp = await self.client.post("/api/tasks", json=body, timeout=60.0)
            print(f"[HermesAdapter.execute_task] response status={resp.status_code} body={resp.text[:500]}")
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as e:
            print(f"[HermesAdapter.execute_task] timeout: {e}")
            traceback.print_exc()
            raise AdapterError(
                "hermes", "execute_task",
                "请求 Hermes 创建任务接口超时（60 秒无响应），请检查 Hermes 服务是否正常"
            )
        except Exception as e:
            print(f"[HermesAdapter.execute_task] error: {e}")
            traceback.print_exc()
            raise AdapterError("hermes", "execute_task", str(e))

    async def get_task(self, task_id: str) -> dict:
        """查询任务状态与结果"""
        try:
            resp = await self.client.get(f"/api/tasks/{task_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise AdapterError("hermes", "get_task", str(e))

    async def meeting_respond(
        self, agent_id: str, meeting_id: str, topic: str, history: list
    ) -> dict:
        """让 Agent 在会议中发言，返回 {opinion: "..."}"""
        try:
            resp = await self.client.post(
                "/api/meetings/respond",
                json={
                    "agent_id": agent_id,
                    "meeting_id": meeting_id,
                    "topic": topic,
                    "history": history,
                },
            )
            if resp.status_code == 404:
                # Hermes 没有实现 meetings/respond 端点，降级用 chat 接口
                # 构造提示词让 Agent 以会议发言形式回复
                context_str = "\n".join(
                    [f"{m.get('agentName', '用户')}: {m['content']}" for m in history[-10:]]
                )
                prompt = f"""我们正在参加一个关于"{topic}"的会议。
之前的讨论内容：
{context_str}

请针对会议主题"{topic}"发表你的专业意见。"""

                chat_resp = await self.client.post(
                    f"/api/agents/{agent_id}/chat",
                    json={"message": prompt, "context": history[-20:]},
                )
                chat_resp.raise_for_status()
                chat_data = chat_resp.json()
                return {"opinion": chat_data.get("reply", "（暂无意见）")}
            resp.raise_for_status()
            return resp.json()
        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError("hermes", "meeting_respond", str(e))

    # ===== 管理接口 =====

    async def refresh_agent(self, agent_id: str) -> dict:
        """强制重载 Agent 的最新配置"""
        try:
            resp = await self.client.post(f"/api/agents/{agent_id}/refresh")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise AdapterError("hermes", "refresh_agent", str(e))

    async def health_check(self) -> bool:
        """检查 Hermes 连通性，不抛异常"""
        try:
            resp = await self.client.get("/api/health")
            return resp.status_code == 200
        except Exception:
            return False
