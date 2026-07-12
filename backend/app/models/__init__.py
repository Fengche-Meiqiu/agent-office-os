"""
数据库模型定义（V2）
新增：Skill/AgentSkill/TaskLog 表
变更：Task 扩展 result/progress/current_step/skill_ids；Meeting 的 rounds 改为 messages
关键修复：JSON 列使用 MutableList 跟踪变更，解决 SQLAlchemy 脏检查问题
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableList, MutableDict

from app.database import Base


class AgentMarketplace(Base):
    """
    人才市场表（agent_marketplace）
    存储来自各平台的全部 Agent，相当于人才库
    platform_agent_id 存储在源平台的真实 ID（修复身份映射问题）
    """
    __tablename__ = "agent_marketplace"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    title = Column(String, default="")
    platform = Column(String, default="hermes")
    platform_agent_id = Column(String, default="")  # 源平台真实 ID（雇佣时用这个，不用 marketplace.id）
    skills = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    status = Column(String, default="ONLINE")
    description = Column(Text, default="")
    soul = Column(MutableDict.as_mutable(JSON), default=dict)  # 人格数据，由平台同步
    created_at = Column(DateTime, default=datetime.utcnow)

    office_agents = relationship("OfficeAgent", back_populates="marketplace_agent")


class OfficeAgent(Base):
    """
    已雇佣员工表（office_agent）
    platform 字段用于 Adapter 路由：get_adapter(agent.platform)
    agent_skills 关联表支持 Skill 启停/配置/使用统计
    """
    __tablename__ = "office_agent"

    id = Column(String, primary_key=True, index=True)
    marketplace_id = Column(String, ForeignKey("agent_marketplace.id"), nullable=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    title = Column(String, default="")
    platform = Column(String, default="hermes")  # Adapter 路由键
    platform_agent_id = Column(String, default="")  # 源平台真实 ID
    status = Column(String, default="ONLINE")
    hired_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    department = Column(String, default="未分配")
    manager_id = Column(String, nullable=True)

    # Soul 人格
    soul = Column(MutableDict.as_mutable(JSON), default=dict)
    # 技能/工具/记忆（兼容旧字段，新数据走 agent_skills 关联表）
    skills = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    memory = Column(JSON, default=list)
    performance = Column(MutableDict.as_mutable(JSON), default=dict)

    # 关联
    marketplace_agent = relationship("AgentMarketplace", back_populates="office_agents")
    tasks = relationship("Task", back_populates="agent", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="agent", cascade="all, delete-orphan")
    agent_skills = relationship("AgentSkill", back_populates="agent", cascade="all, delete-orphan")


class AgentMapping(Base):
    """
    平台映射表（agent_mapping）
    记录 office_agent 与源平台 Agent 的对应关系
    V2：调用 Adapter 前统一查此表获取真实 platform_agent_id
    """
    __tablename__ = "agent_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    office_agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)
    platform_agent_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    """
    任务表（task）V2 扩展
    新增：result(执行结果)、progress(进度0-100)、current_step(当前步骤)、skill_ids(使用的技能)
    """
    __tablename__ = "task"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False)
    agent_name = Column(String, default="")
    status = Column(String, default="Pending")
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)
    output_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # V2 新增字段
    result = Column(Text, nullable=True)  # 任务执行结果（Webhook task_completed 时写入）
    progress = Column(Integer, default=0)  # 进度 0-100
    current_step = Column(String, nullable=True)  # 当前执行步骤
    skill_ids = Column(JSON, default=list)  # 本任务使用的技能 ID 列表
    platform_task_id = Column(String, nullable=True)  # 源平台返回的任务 ID（Hermes 的 task_id），区别于本地的 result

    # 关联
    agent = relationship("OfficeAgent", back_populates="tasks")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")


class TaskLog(Base):
    """
    任务执行日志表（task_log）V2 新增
    记录 Agent 执行任务过程中的步骤、进度、详情
    数据来源：Hermes 通过 Webhook 回调 task_step/task_progress 事件
    """
    __tablename__ = "task_log"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("task.id"), nullable=False, index=True)
    step = Column(String, default="")  # 步骤名，如"搜索资料"
    detail = Column(Text, default="")  # 详情
    level = Column(String, default="info")  # info / warning / error
    timestamp = Column(DateTime, default=datetime.utcnow)

    # 关联
    task = relationship("Task", back_populates="logs")


class Meeting(Base):
    """
    会议表（meeting）V2 重构
    核心变更：rounds(嵌套轮次) → messages(扁平消息列表)
    使用 MutableList 跟踪 JSON 变更，彻底解决"会议只输出一轮"问题
    """
    __tablename__ = "meeting"

    id = Column(String, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    agent_ids = Column(JSON, default=list)
    status = Column(String, default="created")  # created / running / finished
    # V2：扁平消息列表，替代嵌套的 rounds
    messages = Column(MutableList.as_mutable(JSON), default=list)
    summary = Column(Text, nullable=True)
    decisions = Column(JSON, default=list)
    actions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """
    聊天记录表（chat_history）
    """
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False)
    role = Column(String, nullable=False)  # user / agent
    content = Column(Text, nullable=False)
    # 小白解释：Hermes 返回 suggest_task=true 表示这条回复建议用户用 /task 模式
    suggest_task = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    agent = relationship("OfficeAgent", back_populates="chat_messages")


class Output(Base):
    """
    成果文件表（output）
    统一管理任务成果、会议成果、上传文档
    """
    __tablename__ = "output"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, default="markdown")
    source = Column(String, default="task")  # task / meeting / upload
    content = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EventLog(Base):
    """
    系统事件日志表（event_log）
    """
    __tablename__ = "event_log"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, default="system")
    title = Column(String, nullable=False)
    description = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)


class Skill(Base):
    """
    技能目录表（skill）V2 新增
    平台级技能定义，可被多个 Agent 共享
    数据来源：Adapter.get_skills() 同步后写入
    """
    __tablename__ = "skill"

    id = Column(String, primary_key=True, index=True)  # 如 "market_analysis"
    name = Column(String, nullable=False)  # 显示名 "市场分析"
    description = Column(Text, default="")
    params_schema = Column(MutableDict.as_mutable(JSON), default=dict)  # 参数 JSON Schema
    required_tools = Column(JSON, default=list)  # 依赖的工具名
    source_platform = Column(String, default="hermes")
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentSkill(Base):
    """
    Agent-Skill 关联表（agent_skill）V2 新增
    多对多关系，带启用状态、参数配置、使用统计
    支持启停/配置/回溯使用记录
    """
    __tablename__ = "agent_skill"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False, index=True)
    skill_id = Column(String, ForeignKey("skill.id"), nullable=False, index=True)
    enabled = Column(Boolean, default=True)  # 启用/禁用
    params = Column(MutableDict.as_mutable(JSON), default=dict)  # 该 Agent 的参数配置
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)

    agent = relationship("OfficeAgent", back_populates="agent_skills")
    skill = relationship("Skill")
