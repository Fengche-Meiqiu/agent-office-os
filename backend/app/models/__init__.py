from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AgentMarketplace(Base):
    __tablename__ = "agent_marketplace"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    title = Column(String, default="")
    platform = Column(String, default="Hermes")
    skills = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    status = Column(String, default="ONLINE")
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    office_agents = relationship("OfficeAgent", back_populates="marketplace_agent")


class OfficeAgent(Base):
    __tablename__ = "office_agent"

    id = Column(String, primary_key=True, index=True)
    marketplace_id = Column(String, ForeignKey("agent_marketplace.id"), nullable=True)
    name = Column(String, nullable=False)
    avatar = Column(String, default="")
    title = Column(String, default="")
    platform = Column(String, default="Hermes")
    platform_agent_id = Column(String, default="")
    status = Column(String, default="ONLINE")
    hired_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    department = Column(String, default="Unassigned")
    manager_id = Column(String, nullable=True)
    soul = Column(JSON, default=dict)
    skills = Column(JSON, default=list)
    tools = Column(JSON, default=list)
    memory = Column(JSON, default=list)
    performance = Column(JSON, default=dict)

    marketplace_agent = relationship("AgentMarketplace", back_populates="office_agents")
    tasks = relationship("Task", back_populates="agent")
    chat_messages = relationship("ChatMessage", back_populates="agent")


class AgentMapping(Base):
    __tablename__ = "agent_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    office_agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False)
    platform = Column(String, nullable=False)
    platform_agent_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
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

    agent = relationship("OfficeAgent", back_populates="tasks")


class Meeting(Base):
    __tablename__ = "meeting"

    id = Column(String, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    agent_ids = Column(JSON, default=list)
    status = Column(String, default="created")
    rounds = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    decisions = Column(JSON, default=list)
    actions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, ForeignKey("office_agent.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    agent = relationship("OfficeAgent", back_populates="chat_messages")


class Output(Base):
    __tablename__ = "output"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, default="markdown")
    source = Column(String, default="task")
    content = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, default="system")
    title = Column(String, nullable=False)
    description = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
