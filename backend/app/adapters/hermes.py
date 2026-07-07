import httpx
from app.config import settings


class HermesAdapter:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.HERMES_URL).rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def discover_agents(self) -> list[dict]:
        try:
            resp = await self.client.get("/api/agents")
            resp.raise_for_status()
            payload = resp.json()
            items = payload.get("agents", payload) if isinstance(payload, dict) else payload
            if not isinstance(items, list):
                return []
            return [self._normalize_agent(item) for item in items if isinstance(item, dict)]
        except Exception as exc:
            print(f"[HermesAdapter] discover_agents failed: {exc}")
            return []

    async def get_profile(self, agent_id: str) -> dict:
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}")
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else {}
        except Exception as exc:
            print(f"[HermesAdapter] get_profile failed: {exc}")
            return {}

    async def get_skills(self, agent_id: str) -> list[str]:
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/skills")
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, list) else payload.get("skills", [])
        except Exception as exc:
            print(f"[HermesAdapter] get_skills failed: {exc}")
            return []

    async def get_tools(self, agent_id: str) -> list[dict | str]:
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/tools")
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, list) else payload.get("tools", [])
        except Exception as exc:
            print(f"[HermesAdapter] get_tools failed: {exc}")
            return []

    async def get_memory(self, agent_id: str) -> dict:
        try:
            resp = await self.client.get(f"/api/agents/{agent_id}/memory")
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else {"summary": ""}
        except Exception as exc:
            print(f"[HermesAdapter] get_memory failed: {exc}")
            return {"summary": ""}

    async def chat(self, agent_id: str, message: str) -> dict:
        try:
            resp = await self.client.post(
                f"/api/agents/{agent_id}/chat",
                json={"message": message, "attachments": []},
            )
            resp.raise_for_status()
            payload = resp.json()
            if isinstance(payload, dict):
                return payload
            return {"reply": str(payload)}
        except Exception as exc:
            print(f"[HermesAdapter] chat failed: {exc}")
            return {"reply": f"Unable to reach Hermes agent right now: {exc}", "error": str(exc)}

    async def execute_task(self, agent_id: str, title: str, content: str) -> dict:
        try:
            resp = await self.client.post(
                "/api/tasks",
                json={"agent_id": agent_id, "title": title, "content": content, "attachments": []},
            )
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else {"result": str(payload), "status": "completed"}
        except Exception as exc:
            print(f"[HermesAdapter] execute_task failed: {exc}")
            return {"status": "failed", "error": str(exc)}

    async def get_task(self, task_id: str) -> dict:
        try:
            resp = await self.client.get(f"/api/tasks/{task_id}")
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else {"status": "unknown"}
        except Exception as exc:
            print(f"[HermesAdapter] get_task failed: {exc}")
            return {"status": "unknown", "error": str(exc)}

    async def meeting_respond(self, agent_id: str, meeting_id: str, topic: str, history: list) -> dict:
        try:
            resp = await self.client.post(
                "/api/meetings/respond",
                json={"agent_id": agent_id, "meeting_id": meeting_id, "topic": topic, "history": history},
            )
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, dict) else {"opinion": str(payload)}
        except Exception as exc:
            print(f"[HermesAdapter] meeting_respond failed: {exc}")
            return {"opinion": f"{agent_id} is unavailable: {exc}", "error": str(exc)}

    def _normalize_agent(self, item: dict) -> dict:
        external_id = str(item.get("external_id") or item.get("id") or item.get("agent_id") or "")
        name = item.get("name") or item.get("display_name") or "Unnamed Hermes Agent"
        role = item.get("role") or item.get("title") or "Needs Hermes completion"
        description = item.get("description") or item.get("summary") or "Needs Hermes completion"
        skills = item.get("capabilities") or item.get("skills") or []
        tools = item.get("tools") or []
        status = str(item.get("status") or "unknown").upper()
        if status == "AVAILABLE":
            status = "ONLINE"
        if status not in {"ONLINE", "BUSY", "OFFLINE"}:
            status = "OFFLINE"
        return {
            "id": external_id or f"hermes_{abs(hash(name))}",
            "name": str(name),
            "avatar": item.get("avatar_url") or item.get("avatar") or "",
            "title": str(role),
            "platform": "Hermes",
            "skills": [str(value) for value in skills] if isinstance(skills, list) else [str(skills)],
            "tools": tools if isinstance(tools, list) else [str(tools)],
            "status": status,
            "description": str(description),
        }


hermes_adapter = HermesAdapter()
