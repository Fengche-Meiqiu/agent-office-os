"""
pytest 公共 fixtures
小白解释：这里定义了测试时共用的"准备函数"，比如创建测试用数据库、测试用客户端
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 显式导入 models，确保所有表类注册到 Base.metadata（小白解释：让测试数据库能建出所有表）
import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.adapters.base import BaseAdapter
from app.adapters.registry import _registry


# ===== 测试用 Adapter（不依赖真实 Hermes） =====
class MockAdapter(BaseAdapter):
    """测试用的 Mock Adapter，所有方法返回固定值，不调用真实后端"""

    @property
    def platform_name(self) -> str:
        return "hermes"

    async def discover_agents(self) -> list[dict]:
        """返回 2 个测试 Agent，会议需要至少 2 人才能创建"""
        return [
            {
                "id": "mock_agent_001",
                "name": "TestAgent",
                "title": "测试 Agent",
                "platform": "hermes",
                "platform_agent_id": "mock_agent_001",
                "skills": ["测试技能"],
                "tools": ["测试工具"],
                "status": "ONLINE",
                "description": "测试用 Agent",
            },
            {
                "id": "mock_agent_002",
                "name": "TestAgent2",
                "title": "测试 Agent 2",
                "platform": "hermes",
                "platform_agent_id": "mock_agent_002",
                "skills": ["分析技能"],
                "tools": ["搜索工具"],
                "status": "ONLINE",
                "description": "第二个测试用 Agent",
            }
        ]

    async def get_profile(self, agent_id: str) -> dict:
        return {"id": agent_id, "name": "TestAgent", "title": "测试 Agent"}

    async def get_skills(self, agent_id: str) -> list[dict]:
        return [{"id": "skill_1", "name": "测试技能", "description": "用于测试"}]

    async def get_tools(self, agent_id: str) -> list[str]:
        return ["测试工具"]

    async def get_memory(self, agent_id: str) -> list[str]:
        return []

    async def chat(self, agent_id: str, message: str, context: list[dict] = None) -> dict:
        return {"reply": f"收到消息：{message}"}

    async def execute_task(self, agent_id: str, title: str, content: str, skills: list[str] = None) -> dict:
        return {"task_id": "mock_task_001", "status": "running"}

    async def get_task(self, task_id: str) -> dict:
        return {"task_id": task_id, "status": "running", "progress": 50}

    async def meeting_respond(self, agent_id: str, meeting_id: str, topic: str, history: list) -> dict:
        return {"opinion": f"关于{topic}，我同意。"}

    async def refresh_agent(self, agent_id: str) -> dict:
        return {"status": "refreshed"}

    async def health_check(self) -> bool:
        return True


# ===== 测试用 MockAdapter（用于注册表测试，platform_name 不同） =====
class MockAdapterTest(BaseAdapter):
    """另一个 Mock Adapter，platform_name 为 'test_platform'，用于注册表测试"""

    @property
    def platform_name(self) -> str:
        return "test_platform"

    async def discover_agents(self) -> list[dict]:
        return []

    async def get_profile(self, agent_id: str) -> dict:
        return {}

    async def get_skills(self, agent_id: str) -> list[dict]:
        return []

    async def get_tools(self, agent_id: str) -> list[str]:
        return []

    async def get_memory(self, agent_id: str) -> list[str]:
        return []

    async def chat(self, agent_id: str, message: str, context: list[dict] = None) -> dict:
        return {"reply": ""}

    async def execute_task(self, agent_id: str, title: str, content: str, skills: list[str] = None) -> dict:
        return {"task_id": ""}

    async def get_task(self, task_id: str) -> dict:
        return {}

    async def meeting_respond(self, agent_id: str, meeting_id: str, topic: str, history: list) -> dict:
        return {"opinion": ""}

    async def refresh_agent(self, agent_id: str) -> dict:
        return {}

    async def health_check(self) -> bool:
        return False


# ===== 测试数据库 fixture =====
@pytest.fixture
def test_db():
    """
    创建内存级 SQLite 测试数据库，测试完自动销毁
    小白解释：用 StaticPool 让所有线程共享同一个内存数据库，
    否则 TestClient 在另一个线程跑 ASGI app 时会看到空数据库（表都不存在）
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 关键：让内存数据库跨线程共享
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


# ===== 测试客户端 fixture =====
@pytest.fixture
def client(test_db):
    """
    创建 FastAPI 测试客户端，使用内存数据库 + Mock Adapter
    小白解释：TestClient 启动时会触发 lifespan，lifespan 会注册真实的 HermesAdapter，
    所以在 lifespan 之后必须把 MockAdapter 覆盖回去，否则 API 会去连真实的 Hermes
    """
    _registry["hermes"] = MockAdapter()

    # 覆盖 get_db 依赖，用测试数据库
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        # 关键：lifespan 的 init_adapters() 会注册真实 HermesAdapter，这里覆盖回 Mock
        _registry["hermes"] = MockAdapter()
        yield c

    app.dependency_overrides.clear()
    # 清理注册表，不影响其他测试
    _registry.pop("hermes", None)


# ===== 注册 Mock Adapter 的 fixture（在测试开始前执行） =====
@pytest.fixture(autouse=True)
def setup_mock_adapter():
    """自动在每条测试前注册 Mock Adapter"""
    _registry["hermes"] = MockAdapter()
    yield
    _registry.pop("hermes", None)
