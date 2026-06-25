"""
Pydantic Schemas（请求/响应数据模型）
定义 API 接口的输入输出格式，自动生成 OpenAPI 文档
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ===== 人才市场 =====
class MarketplaceAgentOut(BaseModel):
    """人才市场 Agent 响应模型"""
    id: str
    name: str
    avatar: str = ""
    title: str = ""
    platform: str = "Hermes"
    skills: list[str] = []
    tools: list[str] = []
    status: str = "ONLINE"
    description: str = ""

    class Config:
        from_attributes = True


# ===== 办公室 Agent =====
class SoulSchema(BaseModel):
    """Agent 人格信息"""
    identity: str = ""
    goal: str = ""
    principles: str = ""
    style: str = ""
    description: str = ""


class PerformanceSchema(BaseModel):
    """Agent 绩效统计"""
    totalTasks: int = 0
    successTasks: int = 0
    failedTasks: int = 0
    meetingCount: int = 0


class OfficeAgentOut(BaseModel):
    """办公室 Agent 响应模型"""
    id: str
    marketplaceId: Optional[str] = None
    name: str
    avatar: str = ""
    title: str = ""
    platform: str = "Hermes"
    platformAgentId: str = ""
    status: str = "ONLINE"
    hiredAt: Optional[str] = None
    lastActiveAt: Optional[str] = None
    department: str = "未分配"
    managerId: Optional[str] = None
    soul: SoulSchema = SoulSchema()
    skills: list[str] = []
    tools: list[str] = []
    memory: list[str] = []
    performance: PerformanceSchema = PerformanceSchema()

    class Config:
        from_attributes = True


class HireRequest(BaseModel):
    """雇佣 Agent 请求"""
    agentId: str = Field(..., description="人才市场 Agent ID")


# ===== 任务 =====
class TaskOut(BaseModel):
    """任务响应模型"""
    id: str
    name: str
    agentId: str
    agentName: str = ""
    status: str = "Pending"
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    duration: Optional[int] = None
    outputId: Optional[str] = None

    class Config:
        from_attributes = True


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    title: str
    content: str = ""
    agentId: str = ""


# ===== 会议 =====
class MeetingMessageSchema(BaseModel):
    """会议消息"""
    role: str = "agent"  # user / agent
    agentId: Optional[str] = None
    agentName: Optional[str] = None
    content: str
    timestamp: str


class MeetingRoundSchema(BaseModel):
    """会议轮次"""
    round: int
    name: str
    messages: list[MeetingMessageSchema] = []


class MeetingOut(BaseModel):
    """会议响应模型"""
    id: str
    topic: str
    agentIds: list[str] = []
    status: str = "created"
    rounds: list[MeetingRoundSchema] = []
    summary: Optional[str] = None
    decisions: list[str] = []
    actions: list[str] = []
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True


class MeetingCreateRequest(BaseModel):
    """创建会议请求"""
    topic: str
    agentIds: list[str] = Field(..., min_length=2, max_length=10)


class MeetingMessageRequest(BaseModel):
    """主持人插话请求"""
    content: str


# ===== 聊天 =====
class ChatMessageOut(BaseModel):
    """聊天消息响应"""
    id: str
    agentId: str
    role: str
    content: str
    timestamp: str

    class Config:
        from_attributes = True


class ChatSendRequest(BaseModel):
    """发送聊天消息请求"""
    content: str


# ===== 成果 =====
class OutputOut(BaseModel):
    """成果文件响应"""
    id: str
    name: str
    type: str = "markdown"
    source: str = "task"
    content: Optional[str] = None
    url: Optional[str] = None
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True


# ===== 事件日志 =====
class EventLogOut(BaseModel):
    """系统事件响应"""
    id: str
    type: str = "system"
    title: str
    description: str = ""
    timestamp: str

    class Config:
        from_attributes = True


# ===== Webhook =====
class WebhookPayload(BaseModel):
    """Hermes Webhook 回调数据"""
    event: str  # task_created / task_started / task_completed / task_failed / agent_online / agent_offline
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
