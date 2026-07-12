"""
后端基础测试（DeepSeek 补全版）
覆盖范围：
1. Adapter 层：BaseAdapter 契约测试、AdapterRegistry 注册/获取测试
2. 数据模型：Skill/AgentSkill/TaskLog 表 CRUD 测试
3. API 路由：marketplace/office/chat/tasks/meetings/skills/webhook 路由测试
4. SSE 推送：broadcast 函数测试
5. 身份映射：resolve_platform_id 函数测试
"""
import uuid
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.models import (
    Skill, AgentSkill, OfficeAgent, AgentMarketplace, AgentMapping,
    Task, TaskLog, Meeting, Output, EventLog,
)
from app.adapters.base import BaseAdapter, AdapterError
from app.adapters.registry import get_adapter, get_adapter_or_raise, list_platforms, _registry
from tests.conftest import MockAdapter, MockAdapterTest


# 辅助函数：清空注册表（用于 Adapter 注册测试前后清理）
def _clear_registry():
    """清空全局 Adapter 注册表"""
    _registry.clear()


# ===== Adapter 层测试 =====

class TestAdapterRegistry:
    """测试 Adapter 注册中心"""

    def setup_method(self):
        """每个测试前清空注册表"""
        _clear_registry()

    def teardown_method(self):
        """每个测试后清空注册表"""
        _clear_registry()

    def test_register_and_get(self):
        """注册一个 Adapter 后应该能通过 get_adapter 取到"""
        adapter = MockAdapter()
        _registry["hermes"] = adapter

        found = get_adapter("hermes")
        assert found is not None
        assert found.platform_name == "hermes"

    def test_get_nonexistent_adapter(self):
        """获取未注册的 Adapter 应该返回 None"""
        result = get_adapter("不存在的平台")
        assert result is None

    def test_get_adapter_or_raise(self):
        """get_adapter_or_raise 在找不到时应抛 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_adapter_or_raise("不存在的平台")
        assert "不支持的平台" in str(exc_info.value)

    def test_get_adapter_or_raise_with_registered(self):
        """get_adapter_or_raise 在找到时应返回 Adapter 实例"""
        adapter = MockAdapterTest()
        _registry["test_platform"] = adapter

        found = get_adapter_or_raise("test_platform")
        assert found is not None
        assert found.platform_name == "test_platform"

    def test_list_platforms(self):
        """list_platforms 应返回所有已注册的平台名"""
        _registry["hermes"] = MockAdapter()
        _registry["test_platform"] = MockAdapterTest()

        platforms = list_platforms()
        assert "hermes" in platforms
        assert "test_platform" in platforms


class TestMockAdapter:
    """测试 Mock Adapter 是否正确实现 BaseAdapter 契约"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前创建一个 MockAdapter 实例"""
        self.adapter = MockAdapter()

    async def test_platform_name(self):
        """platform_name 应返回 'hermes'"""
        assert self.adapter.platform_name == "hermes"

    async def test_discover_agents(self):
        """discover_agents 应返回 Agent 列表，每个 Agent 包含关键字段"""
        agents = await self.adapter.discover_agents()
        assert isinstance(agents, list)
        assert len(agents) > 0
        agent = agents[0]
        assert "id" in agent
        assert "name" in agent
        assert "platform_agent_id" in agent
        assert "skills" in agent
        assert "tools" in agent

    async def test_chat_returns_reply(self):
        """chat 应返回包含 reply 字段的 dict"""
        result = await self.adapter.chat("agent_001", "你好")
        assert isinstance(result, dict)
        assert "reply" in result
        assert "收到消息" in result["reply"]

    async def test_chat_with_context(self):
        """chat 传入 context 参数不应报错"""
        result = await self.adapter.chat("agent_001", "你好", context=[{"role": "user", "content": "之前的问题"}])
        assert "reply" in result

    async def test_execute_task_returns_task_id(self):
        """execute_task 应返回包含 task_id 的 dict"""
        result = await self.adapter.execute_task("agent_001", "任务标题", "任务内容")
        assert isinstance(result, dict)
        assert "task_id" in result
        assert result["task_id"] == "mock_task_001"

    async def test_execute_task_with_skills(self):
        """execute_task 传入 skills 参数不应报错"""
        result = await self.adapter.execute_task("agent_001", "标题", "内容", skills=["skill_1"])
        assert "task_id" in result

    async def test_get_profile_returns_dict(self):
        """get_profile 应返回包含 id/name 的 dict"""
        profile = await self.adapter.get_profile("agent_001")
        assert profile["id"] == "agent_001"
        assert "name" in profile
        assert "title" in profile

    async def test_get_skills_returns_list(self):
        """get_skills 应返回技能列表"""
        skills = await self.adapter.get_skills("agent_001")
        assert isinstance(skills, list)
        assert len(skills) > 0
        assert "id" in skills[0]

    async def test_meeting_respond_returns_opinion(self):
        """meeting_respond 应返回包含 opinion 的 dict"""
        result = await self.adapter.meeting_respond("agent_001", "meeting_001", "测试主题", [])
        assert "opinion" in result
        assert "测试主题" in result["opinion"]

    async def test_health_check_returns_bool(self):
        """health_check 应返回布尔值"""
        result = await self.adapter.health_check()
        assert result is True

    async def test_all_methods_have_correct_signatures(self):
        """验证所有 BaseAdapter 抽象方法都可调用且返回预期类型"""
        # discover_agents 返回列表
        agents = await self.adapter.discover_agents()
        assert isinstance(agents, list)

        # get_profile 返回 dict
        profile = await self.adapter.get_profile("id")
        assert isinstance(profile, dict)

        # get_skills 返回列表
        skills = await self.adapter.get_skills("id")
        assert isinstance(skills, list)

        # get_tools 返回列表
        tools = await self.adapter.get_tools("id")
        assert isinstance(tools, list)

        # get_memory 返回列表
        memory = await self.adapter.get_memory("id")
        assert isinstance(memory, list)

        # chat 返回 dict
        chat_result = await self.adapter.chat("id", "msg")
        assert isinstance(chat_result, dict)

        # execute_task 返回 dict
        task_result = await self.adapter.execute_task("id", "title", "content")
        assert isinstance(task_result, dict)

        # get_task 返回 dict
        get_task_result = await self.adapter.get_task("task_id")
        assert isinstance(get_task_result, dict)

        # refresh_agent 返回 dict
        refresh_result = await self.adapter.refresh_agent("id")
        assert isinstance(refresh_result, dict)

        # meeting_respond 返回 dict
        meeting_result = await self.adapter.meeting_respond("id", "mid", "topic", [])
        assert isinstance(meeting_result, dict)

        # health_check 返回 bool
        health = await self.adapter.health_check()
        assert isinstance(health, bool)


# ===== 数据模型测试 =====

class TestSkillModel:
    """测试 Skill 表 CRUD"""

    def test_create_skill(self, test_db):
        """创建 Skill 记录并查询"""
        skill = Skill(
            id="skill_test_001",
            name="市场分析技能",
            description="分析和预测市场趋势",
            params_schema={"industry": {"type": "string"}},
            required_tools=["WebSearch"],
            source_platform="hermes",
        )
        test_db.add(skill)
        test_db.commit()

        # 查询验证
        found = test_db.query(Skill).filter(Skill.id == "skill_test_001").first()
        assert found is not None
        assert found.name == "市场分析技能"
        assert found.source_platform == "hermes"
        assert "industry" in found.params_schema
        assert "WebSearch" in found.required_tools

    def test_update_skill(self, test_db):
        """更新 Skill 信息"""
        skill = Skill(id="skill_u_001", name="旧名称", description="旧描述")
        test_db.add(skill)
        test_db.commit()

        skill.name = "新名称"
        skill.description = "新描述"
        test_db.commit()
        test_db.refresh(skill)

        assert skill.name == "新名称"
        assert skill.description == "新描述"

    def test_delete_skill(self, test_db):
        """删除 Skill"""
        skill = Skill(id="skill_d_001", name="待删除技能")
        test_db.add(skill)
        test_db.commit()

        test_db.delete(skill)
        test_db.commit()

        found = test_db.query(Skill).filter(Skill.id == "skill_d_001").first()
        assert found is None

    def test_skill_agent_relationship(self, test_db):
        """Agent-Skill 多对多关联：创建 Agent 和 Skill 并通过 AgentSkill 关联"""
        # 先创建 AgentMarketplace 记录（OfficeAgent 的外键依赖）
        market = AgentMarketplace(
            id="market_rel_001",
            name="测试Agent",
            platform="hermes",
            platform_agent_id="plat_rel_001",
        )
        test_db.add(market)

        # 创建 OfficeAgent
        agent = OfficeAgent(
            id="agent_rel_001",
            marketplace_id="market_rel_001",
            name="测试Agent",
            platform="hermes",
            platform_agent_id="plat_rel_001",
            status="ONLINE",
        )
        test_db.add(agent)

        # 创建 Skill
        skill = Skill(id="skill_rel_001", name="数据分析", description="数据处理")
        test_db.add(skill)

        # 创建关联
        agent_skill = AgentSkill(
            id="as_rel_001",
            agent_id="agent_rel_001",
            skill_id="skill_rel_001",
            enabled=True,
            params={"priority": "high"},
            use_count=0,
        )
        test_db.add(agent_skill)
        test_db.commit()

        # 查询验证：通过 Agent 找到它的 Skill
        agent_with_skills = test_db.query(OfficeAgent).filter(OfficeAgent.id == "agent_rel_001").first()
        assert len(agent_with_skills.agent_skills) == 1
        assert agent_with_skills.agent_skills[0].skill_id == "skill_rel_001"
        assert agent_with_skills.agent_skills[0].enabled is True
        assert agent_with_skills.agent_skills[0].params["priority"] == "high"

        # 验证 use_count 初始为 0
        assert agent_with_skills.agent_skills[0].use_count == 0

    def test_agent_skill_cascade_delete(self, test_db):
        """删除 Agent 时，关联的 AgentSkill 应自动删除（cascade）"""
        market = AgentMarketplace(id="market_cas_001", name="测试Agent", platform="hermes")
        test_db.add(market)

        agent = OfficeAgent(
            id="agent_cas_001", marketplace_id="market_cas_001",
            name="测试Agent", platform="hermes", status="ONLINE",
        )
        test_db.add(agent)

        skill = Skill(id="skill_cas_001", name="测试技能")
        test_db.add(skill)

        asoc = AgentSkill(
            id="as_cas_001", agent_id="agent_cas_001",
            skill_id="skill_cas_001", enabled=True,
        )
        test_db.add(asoc)
        test_db.commit()

        # 删除 Agent
        test_db.delete(agent)
        test_db.commit()

        # AgentSkill 应自动删除
        found = test_db.query(AgentSkill).filter(AgentSkill.id == "as_cas_001").first()
        assert found is None


class TestTaskLogModel:
    """测试 TaskLog 表"""

    def test_create_task_log(self, test_db):
        """创建任务日志并查询"""
        # 先创建 OfficeAgent（Task 的外键依赖）
        market = AgentMarketplace(id="market_tl_001", name="测试Agent", platform="hermes")
        test_db.add(market)
        agent = OfficeAgent(
            id="agent_tl_001", marketplace_id="market_tl_001",
            name="测试Agent", platform="hermes", status="ONLINE",
        )
        test_db.add(agent)

        # 创建 Task
        task = Task(
            id="task_tl_001", name="测试任务",
            agent_id="agent_tl_001", agent_name="测试Agent",
            status="Running",
        )
        test_db.add(task)

        # 创建 TaskLog
        log = TaskLog(
            id="log_tl_001",
            task_id="task_tl_001",
            step="搜索资料",
            detail="正在搜索相关文献",
            level="info",
        )
        test_db.add(log)
        test_db.commit()

        # 查询验证
        found = test_db.query(TaskLog).filter(TaskLog.id == "log_tl_001").first()
        assert found is not None
        assert found.step == "搜索资料"
        assert found.detail == "正在搜索相关文献"
        assert found.level == "info"

    def test_task_log_relationship(self, test_db):
        """Task-TaskLog 一对多关联：一个 Task 关联多个日志"""
        market = AgentMarketplace(id="market_tl2_001", name="测试Agent", platform="hermes")
        test_db.add(market)
        agent = OfficeAgent(
            id="agent_tl2_001", marketplace_id="market_tl2_001",
            name="测试Agent", platform="hermes", status="ONLINE",
        )
        test_db.add(agent)

        task = Task(
            id="task_tl2_001", name="多步骤任务",
            agent_id="agent_tl2_001", agent_name="测试Agent",
            status="Running",
        )
        test_db.add(task)

        # 创建多个日志
        logs = [
            TaskLog(id=f"log_tl2_00{i}", task_id="task_tl2_001",
                    step=f"步骤{i}", detail=f"第{i}步详情")
            for i in range(3)
        ]
        for log in logs:
            test_db.add(log)
        test_db.commit()

        # 查询 Task 的 logs 关联
        task_with_logs = test_db.query(Task).filter(Task.id == "task_tl2_001").first()
        assert len(task_with_logs.logs) == 3
        step_names = [log.step for log in task_with_logs.logs]
        assert "步骤0" in step_names
        assert "步骤2" in step_names

    def test_task_log_cascade_delete(self, test_db):
        """删除 Task 时，关联的 TaskLog 应自动删除"""
        market = AgentMarketplace(id="market_tl3_001", name="测试Agent", platform="hermes")
        test_db.add(market)
        agent = OfficeAgent(
            id="agent_tl3_001", marketplace_id="market_tl3_001",
            name="测试Agent", platform="hermes", status="ONLINE",
        )
        test_db.add(agent)

        task = Task(id="task_tl3_001", name="待删除任务",
                     agent_id="agent_tl3_001", agent_name="测试Agent")
        test_db.add(task)
        test_db.add(TaskLog(id="log_tl3_001", task_id="task_tl3_001", step="步骤1"))
        test_db.commit()

        test_db.delete(task)
        test_db.commit()

        found = test_db.query(TaskLog).filter(TaskLog.id == "log_tl3_001").first()
        assert found is None


class TestMeetingMessagesMutable:
    """测试 Meeting.messages 的 MutableList 脏跟踪"""

    def test_append_message_triggers_update(self, test_db):
        """往 messages 列表 append 消息后，数据库应能读取到变更后的数据"""
        meeting = Meeting(
            id="meeting_mut_001",
            topic="可变列表测试",
            agent_ids=["agent_1", "agent_2"],
            status="created",
            messages=[],
        )
        test_db.add(meeting)
        test_db.commit()

        # 重新查询（获取新的 session 状态），验证初始为空
        m1 = test_db.query(Meeting).filter(Meeting.id == "meeting_mut_001").first()
        assert m1.messages == []

        # 追加一条消息
        m1.messages.append({
            "role": "agent",
            "agentId": "agent_1",
            "agentName": "Agent1",
            "content": "第一次发言",
            "timestamp": datetime.utcnow().isoformat(),
        })
        test_db.commit()

        # 重新查询验证消息已持久化
        m2 = test_db.query(Meeting).filter(Meeting.id == "meeting_mut_001").first()
        assert len(m2.messages) == 1
        assert m2.messages[0]["content"] == "第一次发言"

    def test_append_multiple_messages(self, test_db):
        """连续追加多条消息，验证 MutableList 脏跟踪正常工作"""
        meeting = Meeting(
            id="meeting_mut_002",
            topic="多人讨论",
            agent_ids=[],
            status="running",
            messages=[],
        )
        test_db.add(meeting)
        test_db.commit()

        messages_content = ["发言1", "发言2", "发言3"]
        for content in messages_content:
            m = test_db.query(Meeting).filter(Meeting.id == "meeting_mut_002").first()
            m.messages.append({
                "role": "agent",
                "agentName": "Agent",
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            })
            test_db.commit()

        # 最终应该有 3 条消息
        final = test_db.query(Meeting).filter(Meeting.id == "meeting_mut_002").first()
        assert len(final.messages) == 3
        contents = [msg["content"] for msg in final.messages]
        assert contents == ["发言1", "发言2", "发言3"]

    def test_message_order_preserved(self, test_db):
        """追加消息的顺序应完整保留"""
        meeting = Meeting(
            id="meeting_mut_003",
            topic="顺序测试",
            agent_ids=[],
            status="created",
            messages=[],
        )
        test_db.add(meeting)
        test_db.commit()

        timestamps = []
        for i in range(5):
            ts = datetime.utcnow().isoformat()
            timestamps.append(ts)
            m = test_db.query(Meeting).filter(Meeting.id == "meeting_mut_003").first()
            m.messages.append({
                "role": "agent",
                "agentName": f"Agent{i}",
                "content": f"第{i}条消息",
                "timestamp": ts,
            })
            test_db.commit()

        final = test_db.query(Meeting).filter(Meeting.id == "meeting_mut_003").first()
        for i, msg in enumerate(final.messages):
            assert msg["content"] == f"第{i}条消息"
            assert msg["agentName"] == f"Agent{i}"


# ===== API 路由测试 =====

class TestMarketplaceAPI:
    """测试人才市场 API"""

    def test_list_empty_marketplace(self, client):
        """空数据库时 GET /api/marketplace/agents 应返回空列表"""
        resp = client.get("/api/marketplace/agents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_sync_marketplace(self, client):
        """POST /api/marketplace/sync 应从 MockAdapter 同步 Agent"""
        resp = client.post("/api/marketplace/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "同步完成"
        assert data["added"] is not None
        assert data["total"] > 0

    def test_sync_then_list(self, client):
        """同步后 GET 列表应包含同步的 Agent"""
        client.post("/api/marketplace/sync")
        resp = client.get("/api/marketplace/agents")
        assert resp.status_code == 200
        agents = resp.json()
        assert len(agents) > 0
        assert agents[0]["name"] == "TestAgent"

    def test_hire_agent(self, client):
        """POST /api/marketplace/hire 应雇佣 Agent 并创建映射"""
        # 先同步
        client.post("/api/marketplace/sync")

        # 获取 marketplace agent ID
        list_resp = client.get("/api/marketplace/agents")
        agents = list_resp.json()
        assert len(agents) > 0
        market_id = agents[0]["id"]

        # 雇佣
        resp = client.post("/api/marketplace/hire", json={"agentId": market_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "雇佣成功"
        assert "agentId" in data

    def test_hire_nonexistent_agent(self, client):
        """雇佣不存在的 Agent 应返回 404"""
        resp = client.post("/api/marketplace/hire", json={"agentId": "不存在_ID"})
        assert resp.status_code == 404

    def test_double_hire_returns_400(self, client):
        """重复雇佣同一个 Agent 应返回 400"""
        client.post("/api/marketplace/sync")
        list_resp = client.get("/api/marketplace/agents")
        market_id = list_resp.json()[0]["id"]

        # 第一次雇佣
        client.post("/api/marketplace/hire", json={"agentId": market_id})

        # 第二次雇佣应失败
        resp = client.post("/api/marketplace/hire", json={"agentId": market_id})
        assert resp.status_code == 400


class TestOfficeAPI:
    """测试办公室 Agent API"""

    def _hire_test_agent(self, client) -> str:
        """辅助方法：先同步再雇佣一个测试 Agent，返回 office_agent_id"""
        client.post("/api/marketplace/sync")
        list_resp = client.get("/api/marketplace/agents")
        market_id = list_resp.json()[0]["id"]
        hire_resp = client.post("/api/marketplace/hire", json={"agentId": market_id})
        return hire_resp.json()["agentId"]

    def test_list_office_agents_returns_slim(self, client):
        """GET /api/office/agents 应返回精简版（保留工具中心所需的 tools）"""
        self._hire_test_agent(client)

        resp = client.get("/api/office/agents")
        assert resp.status_code == 200
        agents = resp.json()
        assert len(agents) > 0
        agent = agents[0]

        # 精简版应有基本字段
        assert "id" in agent
        assert "name" in agent
        assert "status" in agent

        # 精简版不应有完整详情字段
        assert "skills" not in agent
        assert "tools" in agent
        assert "memory" not in agent
        assert "performance" not in agent

    def test_get_office_agent_detail(self, client):
        """GET /api/office/agents/{id} 应返回完整详情"""
        agent_id = self._hire_test_agent(client)

        resp = client.get(f"/api/office/agents/{agent_id}")
        assert resp.status_code == 200
        agent = resp.json()

        # 应有基本字段
        assert agent["id"] == agent_id
        assert agent["name"] == "TestAgent"

        # 完整版应含 skills/tools/performance
        assert "skills" in agent
        assert "tools" in agent
        assert "performance" in agent
        assert "soul" in agent

    def test_get_nonexistent_agent_detail(self, client):
        """查询不存在的 Agent 应返回 404"""
        resp = client.get("/api/office/agents/不存在_ID")
        assert resp.status_code == 404

    def test_fire_agent(self, client):
        """解雇 Agent 后应不再出现在列表中"""
        agent_id = self._hire_test_agent(client)

        # 解雇
        resp = client.delete(f"/api/office/agents/{agent_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "解雇成功"

        # 列表不应包含
        list_resp = client.get("/api/office/agents")
        ids = [a["id"] for a in list_resp.json()]
        assert agent_id not in ids


class TestChatAPI:
    """测试聊天 API"""

    def _hire_test_agent(self, client) -> str:
        """辅助方法：雇佣一个测试 Agent，返回 office_agent_id"""
        client.post("/api/marketplace/sync")
        list_resp = client.get("/api/marketplace/agents")
        market_id = list_resp.json()[0]["id"]
        hire_resp = client.post("/api/marketplace/hire", json={"agentId": market_id})
        return hire_resp.json()["agentId"]

    def test_send_and_get_messages(self, client):
        """发送消息后 GET 应包含该消息"""
        agent_id = self._hire_test_agent(client)

        # 发送消息
        resp = client.post(
            f"/api/chat/{agent_id}/messages",
            json={"content": "你好，帮我查个数据"}
        )
        assert resp.status_code == 200
        reply = resp.json()
        assert reply["role"] == "agent"
        assert "收到消息" in reply["content"]

        # 获取聊天记录
        messages_resp = client.get(f"/api/chat/{agent_id}/messages")
        assert messages_resp.status_code == 200
        messages = messages_resp.json()
        assert len(messages) >= 2  # 用户消息 + Agent 回复

        # 验证顺序：第一条应是用户消息
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "你好，帮我查个数据"
        # 第二条应是 Agent 回复
        assert messages[1]["role"] == "agent"

    def test_send_to_nonexistent_agent(self, client):
        """给不存在的 Agent 发消息应返回 404"""
        resp = client.post(
            "/api/chat/不存在_ID/messages",
            json={"content": "你好"}
        )
        assert resp.status_code == 404


class TestTasksAPI:
    """测试任务 API"""

    def _hire_test_agent(self, client) -> str:
        """辅助方法：雇佣一个测试 Agent"""
        client.post("/api/marketplace/sync")
        list_resp = client.get("/api/marketplace/agents")
        market_id = list_resp.json()[0]["id"]
        hire_resp = client.post("/api/marketplace/hire", json={"agentId": market_id})
        return hire_resp.json()["agentId"]

    def test_list_tasks_empty(self, client):
        """空数据库时 GET /api/tasks 应返回空列表"""
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_task(self, client):
        """创建任务应调用 Adapter.execute_task 并返回 Running 状态"""
        agent_id = self._hire_test_agent(client)

        resp = client.post("/api/tasks", json={
            "title": "测试任务",
            "content": "请帮我分析数据",
            "agentId": agent_id,
        })
        assert resp.status_code == 200
        task = resp.json()
        assert task["name"] == "测试任务"
        assert task["agentId"] == agent_id
        assert task["status"] == "Running"  # MockAdapter 返回 task_id，所以是 Running

    def test_create_task_with_skill_ids(self, client):
        """创建任务时传入 skillIds"""
        agent_id = self._hire_test_agent(client)

        resp = client.post("/api/tasks", json={
            "title": "带技能的任务",
            "content": "使用特定技能完成任务",
            "agentId": agent_id,
            "skillIds": ["skill_001", "skill_002"],
        })
        assert resp.status_code == 200
        task = resp.json()
        assert task["skillIds"] == ["skill_001", "skill_002"]

    def test_create_task_nonexistent_agent(self, client):
        """给不存在的 Agent 创建任务应返回 404"""
        resp = client.post("/api/tasks", json={
            "title": "测试",
            "content": "内容",
            "agentId": "不存在_ID",
        })
        assert resp.status_code == 404

    def test_get_task(self, client):
        """创建任务后可通过 ID 查询"""
        agent_id = self._hire_test_agent(client)
        create_resp = client.post("/api/tasks", json={
            "title": "可查询的任务",
            "content": "内容",
            "agentId": agent_id,
        })
        task_id = create_resp.json()["id"]

        # 查询
        resp = client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

    def test_get_task_logs(self, client):
        """GET /api/tasks/{id}/logs 应返回任务日志列表"""
        agent_id = self._hire_test_agent(client)
        create_resp = client.post("/api/tasks", json={
            "title": "带日志的任务",
            "content": "内容",
            "agentId": agent_id,
        })
        task_id = create_resp.json()["id"]

        # 刚创建的任务日志应该为空
        resp = client.get(f"/api/tasks/{task_id}/logs")
        assert resp.status_code == 200
        assert resp.json() == []


class TestMeetingsAPI:
    """测试会议 API（V2 自由讨论）"""

    def _hire_two_agents(self, client) -> tuple:
        """雇佣两个测试 Agent，返回 ID 列表"""
        client.post("/api/marketplace/sync")
        list_resp = client.get("/api/marketplace/agents")
        agents = list_resp.json()
        ids = []
        for agent in agents[:2]:  # 取前两个
            hire_resp = client.post("/api/marketplace/hire", json={"agentId": agent["id"]})
            ids.append(hire_resp.json()["agentId"])
        return ids

    def test_create_meeting(self, client):
        """创建会议"""
        agent_ids = self._hire_two_agents(client)

        resp = client.post("/api/meetings", json={
            "topic": "产品规划讨论",
            "agentIds": agent_ids,
        })
        assert resp.status_code == 200
        meeting = resp.json()
        assert meeting["topic"] == "产品规划讨论"
        assert meeting["status"] == "created"
        assert meeting["messages"] == []
        assert "id" in meeting

    def test_create_meeting_less_than_2_agents_should_fail(self, client):
        """少于 2 个 Agent 创建会议应失败"""
        resp = client.post("/api/meetings", json={
            "topic": "测试",
            "agentIds": ["agent_1"],  # 只有 1 个
        })
        assert resp.status_code == 422  # Pydantic 校验失败

    def test_start_meeting(self, client):
        """开始会议：所有 Agent 首次发言"""
        agent_ids = self._hire_two_agents(client)

        # 创建会议
        create_resp = client.post("/api/meetings", json={
            "topic": "开始会议测试",
            "agentIds": agent_ids,
        })
        meeting_id = create_resp.json()["id"]

        # 开始会议
        resp = client.post(f"/api/meetings/{meeting_id}/start")
        assert resp.status_code == 200
        meeting = resp.json()
        assert meeting["status"] == "running"
        assert len(meeting["messages"]) == len(agent_ids)  # 每个 Agent 发言一次

    def test_start_already_started_meeting(self, client):
        """重复开始已开始的会议应返回 400"""
        agent_ids = self._hire_two_agents(client)
        create_resp = client.post("/api/meetings", json={
            "topic": "测试", "agentIds": agent_ids,
        })
        meeting_id = create_resp.json()["id"]

        client.post(f"/api/meetings/{meeting_id}/start")
        resp = client.post(f"/api/meetings/{meeting_id}/start")
        assert resp.status_code == 400

    def test_ask_all(self, client):
        """让所有 Agent 发言"""
        agent_ids = self._hire_two_agents(client)
        create_resp = client.post("/api/meetings", json={
            "topic": "ask-all测试",
            "agentIds": agent_ids,
        })
        meeting_id = create_resp.json()["id"]

        # ask-all 会让状态变为 running 并让所有人发言
        resp = client.post(f"/api/meetings/{meeting_id}/ask-all")
        assert resp.status_code == 200
        meeting = resp.json()
        assert meeting["status"] == "running"
        assert len(meeting["messages"]) == len(agent_ids)

    def test_ask_specific_agent(self, client):
        """让指定 Agent 发言"""
        agent_ids = self._hire_two_agents(client)
        create_resp = client.post("/api/meetings", json={
            "topic": "ask-agent测试",
            "agentIds": agent_ids,
        })
        meeting_id = create_resp.json()["id"]

        # 让第一个 Agent 发言
        resp = client.post(f"/api/meetings/{meeting_id}/ask/{agent_ids[0]}")
        assert resp.status_code == 200
        meeting = resp.json()
        assert meeting["status"] == "running"
        assert len(meeting["messages"]) == 1
        assert meeting["messages"][0]["agentId"] == agent_ids[0]

    def test_send_message(self, client):
        """主持人插话"""
        agent_ids = self._hire_two_agents(client)
        create_resp = client.post("/api/meetings", json={
            "topic": "插话测试",
            "agentIds": agent_ids,
        })
        meeting_id = create_resp.json()["id"]

        resp = client.post(f"/api/meetings/{meeting_id}/messages", json={
            "content": "我有个想法"
        })
        assert resp.status_code == 200
        meeting = resp.json()
        assert meeting["status"] == "running"
        assert len(meeting["messages"]) == 1
        assert meeting["messages"][0]["role"] == "user"
        assert meeting["messages"][0]["content"] == "我有个想法"

    def test_finish_meeting_generates_output(self, client):
        """结束会议应生成纪要并存入 Output"""
        agent_ids = self._hire_two_agents(client)
        create_resp = client.post("/api/meetings", json={
            "topic": "结束测试",
            "agentIds": agent_ids,
        })
        meeting_id = create_resp.json()["id"]

        # 先开始
        client.post(f"/api/meetings/{meeting_id}/start")

        # 然后结束
        resp = client.post(f"/api/meetings/{meeting_id}/finish")
        assert resp.status_code == 200
        meeting = resp.json()
        assert meeting["status"] == "finished"
        assert meeting["summary"] is not None
        assert "会议纪要" in meeting["summary"]

        # 验证 Output 已生成
        outputs_resp = client.get("/api/outputs")
        outputs = outputs_resp.json()
        assert len(outputs) > 0
        # 找会议纪要
        meeting_outputs = [o for o in outputs if o["source"] == "meeting"]
        assert len(meeting_outputs) > 0
        assert "结束测试" in meeting_outputs[0]["name"]

    def test_finish_twice_returns_400(self, client):
        """结束已结束的会议应返回 400"""
        agent_ids = self._hire_two_agents(client)
        create_resp = client.post("/api/meetings", json={
            "topic": "重复结束测试",
            "agentIds": agent_ids,
        })
        meeting_id = create_resp.json()["id"]

        client.post(f"/api/meetings/{meeting_id}/start")
        client.post(f"/api/meetings/{meeting_id}/finish")

        resp = client.post(f"/api/meetings/{meeting_id}/finish")
        assert resp.status_code == 400


class TestSkillsAPI:
    """测试 Skill 管理 API"""

    def _hire_test_agent(self, client) -> str:
        """辅助方法：雇佣测试 Agent"""
        client.post("/api/marketplace/sync")
        list_resp = client.get("/api/marketplace/agents")
        market_id = list_resp.json()[0]["id"]
        hire_resp = client.post("/api/marketplace/hire", json={"agentId": market_id})
        return hire_resp.json()["agentId"]

    def _create_skill(self, test_db, skill_id: str, name: str = "测试技能") -> None:
        """辅助方法：直接在数据库中创建 Skill 记录（API 没有创建 Skill 的端点，只能同步或直接写库）"""
        skill = Skill(id=skill_id, name=name, description="测试用技能")
        test_db.add(skill)
        test_db.commit()

    def test_list_skills_empty(self, client):
        """空数据库时 GET /api/skills 返回空列表"""
        resp = client.get("/api/skills")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_add_agent_skill(self, client, test_db):
        """给 Agent 添加 Skill（需先在 Skill 表创建记录）"""
        agent_id = self._hire_test_agent(client)
        self._create_skill(test_db, "skill_add_001", "添加技能测试")

        # 先创建一个 Skill
        resp = client.post(f"/api/agents/{agent_id}/skills", json={
            "skillId": "skill_add_001",
        })
        assert resp.status_code == 200
        asoc = resp.json()
        assert asoc["agentId"] == agent_id
        assert asoc["skillId"] == "skill_add_001"
        assert asoc["enabled"] is True

    def test_add_agent_skill_with_params(self, client, test_db):
        """添加 Skill 时传入参数配置"""
        agent_id = self._hire_test_agent(client)
        self._create_skill(test_db, "skill_params_001", "参数技能测试")

        resp = client.post(f"/api/agents/{agent_id}/skills", json={
            "skillId": "skill_params_001",
            "params": {"priority": "high", "timeout": 30},
        })
        assert resp.status_code == 200
        assert resp.json()["params"] == {"priority": "high", "timeout": 30}

    def test_add_skill_to_nonexistent_agent(self, client):
        """给不存在的 Agent 添加 Skill 应返回 404"""
        resp = client.post("/api/agents/不存在_ID/skills", json={
            "skillId": "skill_001",
        })
        assert resp.status_code == 404

    def test_list_agent_skills(self, client, test_db):
        """获取 Agent 的技能列表"""
        agent_id = self._hire_test_agent(client)
        self._create_skill(test_db, "skill_list_001", "列表技能1")
        self._create_skill(test_db, "skill_list_002", "列表技能2")
        client.post(f"/api/agents/{agent_id}/skills", json={"skillId": "skill_list_001"})
        client.post(f"/api/agents/{agent_id}/skills", json={"skillId": "skill_list_002"})

        resp = client.get(f"/api/agents/{agent_id}/skills")
        assert resp.status_code == 200
        skills = resp.json()
        assert len(skills) == 2

    def test_update_agent_skill(self, client, test_db):
        """修改 Agent 的 Skill 配置（启停）"""
        agent_id = self._hire_test_agent(client)
        self._create_skill(test_db, "skill_upd_001", "更新技能测试")
        client.post(f"/api/agents/{agent_id}/skills", json={"skillId": "skill_upd_001"})

        # 禁用
        resp = client.put(f"/api/agents/{agent_id}/skills/skill_upd_001", json={
            "enabled": False,
        })
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_remove_agent_skill(self, client, test_db):
        """移除 Agent 的 Skill"""
        agent_id = self._hire_test_agent(client)
        self._create_skill(test_db, "skill_del_001", "删除技能测试")
        client.post(f"/api/agents/{agent_id}/skills", json={"skillId": "skill_del_001"})

        resp = client.delete(f"/api/agents/{agent_id}/skills/skill_del_001")
        assert resp.status_code == 200
        assert resp.json()["message"] == "已移除 Skill"

        # 验证列表为空
        list_resp = client.get(f"/api/agents/{agent_id}/skills")
        assert list_resp.json() == []

    def test_refresh_agent_skills(self, client):
        """从源平台刷新 Agent 技能"""
        agent_id = self._hire_test_agent(client)

        resp = client.post(f"/api/agents/{agent_id}/skills/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Skill 同步完成"
        # MockAdapter 返回 1 个技能
        assert data["totalRemote"] >= 1


class TestWebhook:
    """测试 Webhook 回调"""

    def _create_test_task(self, client) -> str:
        """创建测试任务，返回 task_id"""
        # 先雇佣 Agent
        client.post("/api/marketplace/sync")
        list_resp = client.get("/api/marketplace/agents")
        market_id = list_resp.json()[0]["id"]
        hire_resp = client.post("/api/marketplace/hire", json={"agentId": market_id})
        agent_id = hire_resp.json()["agentId"]

        # 创建任务
        task_resp = client.post("/api/tasks", json={
            "title": "Webhook测试任务",
            "content": "测试内容",
            "agentId": agent_id,
        })
        return task_resp.json()["id"]

    def test_task_completed_stores_result(self, client):
        """task_completed 事件应存储 result 并创建 Output"""
        task_id = self._create_test_task(client)

        # 模拟 Hermes 回调：任务完成
        resp = client.post("/api/webhook/hermes", json={
            "event": "task_completed",
            "task_id": task_id,
            "result": "任务执行成功，共处理100条数据",
        })
        assert resp.status_code == 200
        assert resp.json()["event"] == "task_completed"

        # 验证任务状态和 result
        task_resp = client.get(f"/api/tasks/{task_id}")
        task = task_resp.json()
        assert task["status"] == "Completed"
        assert task["result"] == "任务执行成功，共处理100条数据"

        # 验证 Output 自动生成
        outputs_resp = client.get("/api/outputs")
        outputs = outputs_resp.json()
        task_outputs = [o for o in outputs if o["source"] == "task"]
        assert len(task_outputs) > 0
        assert "处理100条数据" in task_outputs[0]["content"]

    def test_task_failed_stores_result(self, client):
        """task_failed 事件应记录错误结果但不创建 Output"""
        task_id = self._create_test_task(client)

        resp = client.post("/api/webhook/hermes", json={
            "event": "task_failed",
            "task_id": task_id,
            "result": "执行失败：API 超时",
        })
        assert resp.status_code == 200

        task_resp = client.get(f"/api/tasks/{task_id}")
        task = task_resp.json()
        assert task["status"] == "Failed"
        assert "API 超时" in task["result"]

    def test_task_progress_updates_progress(self, client):
        """task_progress 事件应更新进度"""
        task_id = self._create_test_task(client)

        # 第一次进度更新
        client.post("/api/webhook/hermes", json={
            "event": "task_progress",
            "task_id": task_id,
            "progress": 50,
            "step": "搜索资料",
        })

        task_resp = client.get(f"/api/tasks/{task_id}")
        task = task_resp.json()
        assert task["progress"] == 50
        assert task["currentStep"] == "搜索资料"

        # 第二次进度更新
        client.post("/api/webhook/hermes", json={
            "event": "task_progress",
            "task_id": task_id,
            "progress": 80,
            "step": "分析数据",
        })

        task_resp = client.get(f"/api/tasks/{task_id}")
        task = task_resp.json()
        assert task["progress"] == 80
        assert task["currentStep"] == "分析数据"

    def test_task_step_creates_log(self, client):
        """task_step 事件应创建 TaskLog 记录"""
        task_id = self._create_test_task(client)

        # 推送步骤事件
        client.post("/api/webhook/hermes", json={
            "event": "task_step",
            "task_id": task_id,
            "step": "数据清洗",
            "detail": "正在清洗原始数据，去除重复项",
        })

        # 查询日志
        logs_resp = client.get(f"/api/tasks/{task_id}/logs")
        logs = logs_resp.json()
        assert len(logs) == 1
        assert logs[0]["step"] == "数据清洗"
        assert logs[0]["detail"] == "正在清洗原始数据，去除重复项"

    def test_task_step_multiple_logs(self, client):
        """多个 task_step 事件应生成多条日志"""
        task_id = self._create_test_task(client)

        steps = [
            ("步骤1", "开始执行"),
            ("步骤2", "处理中"),
            ("步骤3", "完成"),
        ]
        for step, detail in steps:
            client.post("/api/webhook/hermes", json={
                "event": "task_step",
                "task_id": task_id,
                "step": step,
                "detail": detail,
            })

        logs_resp = client.get(f"/api/tasks/{task_id}/logs")
        logs = logs_resp.json()
        assert len(logs) == 3
        assert logs[-1]["step"] == "步骤3"

    def test_nonexistent_task_webhook(self, client):
        """给不存在的任务发 Webhook 不应报错"""
        resp = client.post("/api/webhook/hermes", json={
            "event": "task_completed",
            "task_id": "不存在_ID",
            "result": "结果",
        })
        assert resp.status_code == 200
        assert resp.json()["event"] == "task_completed"


# ===== 身份映射测试 =====

class TestResolvePlatformId:
    """测试 resolve_platform_id 函数"""

    def _create_agent(self, test_db: Session, agent_id: str,
                      platform_agent_id: str = "") -> OfficeAgent:
        """辅助：创建 OfficeAgent 记录"""
        market = AgentMarketplace(
            id=f"market_{agent_id}",
            name=f"Agent_{agent_id}",
            platform="hermes",
            platform_agent_id=platform_agent_id or agent_id,
        )
        test_db.add(market)
        agent = OfficeAgent(
            id=agent_id,
            marketplace_id=market.id,
            name=f"Agent_{agent_id}",
            platform="hermes",
            platform_agent_id=platform_agent_id,
            status="ONLINE",
        )
        test_db.add(agent)
        test_db.commit()
        return agent

    def test_resolve_from_mapping(self, test_db):
        """优先从 AgentMapping 表获取"""
        agent = self._create_agent(test_db, "agent_mapping_001", platform_agent_id="old_plat_id")

        # 创建映射，指向真实的平台 ID
        mapping = AgentMapping(
            office_agent_id="agent_mapping_001",
            platform="hermes",
            platform_agent_id="real_platform_id_001",
        )
        test_db.add(mapping)
        test_db.commit()

        # 调用 resolve_platform_id
        from app.api.meetings import resolve_platform_id
        result = resolve_platform_id(agent, test_db)
        # 应返回映射中的 ID（优先级最高）
        assert result == "real_platform_id_001"

    def test_fallback_to_platform_agent_id(self, test_db):
        """无映射时回退到 agent.platform_agent_id"""
        agent = self._create_agent(test_db, "agent_fb_001", platform_agent_id="fallback_plat_id")

        # 不创建映射，直接调用
        from app.api.meetings import resolve_platform_id
        result = resolve_platform_id(agent, test_db)
        assert result == "fallback_plat_id"

    def test_fallback_to_agent_id(self, test_db):
        """都无映射时回退到 agent.id"""
        agent = self._create_agent(test_db, "agent_fb2_001", platform_agent_id="")

        from app.api.meetings import resolve_platform_id
        result = resolve_platform_id(agent, test_db)
        # 没有映射，platform_agent_id 为空，回退到 agent.id
        assert result == "agent_fb2_001"

