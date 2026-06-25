"""
数据库模型定义
对应文档中的 10 张数据表
所有表使用 SQLAlchemy 2.0 声明式风格
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class AgentMarketplace(Base):
    """
    人才市场表（agent_marketplace）
    存储来自 Hermes 等平台的全部 Agent
    相当于人才库
    """
    __tablename__ = "agent_marketplace"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    title = Column(String, default="")
    platform = Column(String, default="Hermes")  # Hermes / OpenClaw / CrewAI / LangGraph
    skills = Column(JSON, default=list)  # ["市场分析", "Python开发"]
    tools = Column(JSON, default=list)  # ["web_search", "python"]
    status = Column(String, default="ONLINE")  # ONLINE / OFFLINE / BUSY
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联：一个人才市场 Agent 可以被雇佣为办公室 Agent
    office_agents = relationship("OfficeAgent", back_populates="marketplace_agent")


class OfficeAgent(Base):
    """
    已雇佣员工表（office_agent）
    已经进入 Office 组织架构的 Agent
    拥有工位、任务、会议权限、历史记录
    """
    __tablename__ = "office_agent"

    id = Column(String, primary_key=True, index=True)
    marketplace_id = Column(String, ForeignKey("agent_marketplace.id"), nullable=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    title = Column(String, default="")
    platform = Column(String, default="Hermes")
    platform_agent_id = Column(String, default="")  # 在源平台的 Agent ID
    status = Column(String, default="ONLINE")  # ONLINE / WORKING / MEETING / OFFLINE / ERROR
    hired_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    department = Column(String, default="未分配")
    manager_id = Column(String, nullable=True)  # 直属上级 ID

    # Soul 人格（JSON 存储）
    soul = Column(JSON, default=dict)  # {identity, goal, principles, style, description}
    # 技能列表
    skills = Column(JSON, default=list)
    # 工具能力列表
    tools = Column(JSON, default=list)
    # 记忆摘要列表
    memory = Column(JSON, default=list)
    # 绩效统计
    performance = Column(JSON, default=dict)  # {totalTasks, successTasks, failedTasks, meetingCount}

    # 关联
    marketplace_agent = relationship("AgentMarketplace", back_populates="office_agents")
    tasks = relationship("Task", back_populates="agent")
    chat_messages = relationship("ChatMessage", back_populates="agent")


class AgentMapping(Base):
    """
    平台映射表（agent_mapping）
    记录 office_agent 与源平台 Agent 的对应关系
    """
    __tablename__ = "agent_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    office_agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False)
    platform = Column(String, nullable=False)  # Hermes / OpenClaw 等
    platform_agent_id = Column(String, nullable=False)  # 源平台的 Agent ID
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    """
    任务表（task）
    记录 Agent 执行的任务
    """
    __tablename__ = "task"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False)
    agent_name = Column(String, default="")
    status = Column(String, default="Pending")  # Pending / Running / Completed / Failed / Cancelled
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # 耗时（分钟）
    output_id = Column(String, nullable=True)  # 关联的成果 ID
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    agent = relationship("OfficeAgent", back_populates="tasks")


class Meeting(Base):
    """
    会议表（meeting）
    记录会议基本信息与结果
    """
    __tablename__ = "meeting"

    id = Column(String, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    agent_ids = Column(JSON, default=list)  # 参会 Agent ID 列表
    status = Column(String, default="created")  # created / running / finished
    rounds = Column(JSON, default=list)  # 各轮次讨论内容
    summary = Column(Text, nullable=True)  # 会议纪要
    decisions = Column(JSON, default=list)  # 决策建议
    actions = Column(JSON, default=list)  # 行动项
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """
    聊天记录表（chat_history）
    记录用户与 Agent 的对话
    """
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False)
    role = Column(String, nullable=False)  # user / agent
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # 关联
    agent = relationship("OfficeAgent", back_populates="chat_messages")


class Output(Base):
    """
    成果文件表（output）
    统一管理任务成果、会议成果、上传文档
    """
    __tablename__ = "output"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, default="markdown")  # markdown / pdf / html / image / link
    source = Column(String, default="task")  # task / meeting / upload
    content = Column(Text, nullable=True)  # 文本内容（markdown/html）
    url = Column(String, nullable=True)  # 文件 URL 或外部链接
    created_at = Column(DateTime, default=datetime.utcnow)


class EventLog(Base):
    """
    系统事件日志表（event_log）
    记录系统中的关键事件，用于通知面板展示
    """
    __tablename__ = "event_log"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, default="system")  # task / meeting / system / agent
    title = Column(String, nullable=False)
    description = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
