from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MarketplaceAgentOut(BaseModel):
    id: str
    name: str
    avatar: str = ""
    title: str = ""
    platform: str = "Hermes"
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    status: str = "ONLINE"
    description: str = ""

    model_config = ConfigDict(from_attributes=True)


class SoulSchema(BaseModel):
    identity: str = ""
    goal: str = ""
    principles: str = ""
    style: str = ""
    description: str = ""


class PerformanceSchema(BaseModel):
    totalTasks: int = 0
    successTasks: int = 0
    failedTasks: int = 0
    meetingCount: int = 0


class OfficeAgentOut(BaseModel):
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
    department: str = "Unassigned"
    managerId: Optional[str] = None
    soul: SoulSchema = Field(default_factory=SoulSchema)
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    memory: list[str] = Field(default_factory=list)
    performance: PerformanceSchema = Field(default_factory=PerformanceSchema)

    model_config = ConfigDict(from_attributes=True)


class HireRequest(BaseModel):
    agentId: str = Field(..., description="Marketplace agent id")


class TaskOut(BaseModel):
    id: str
    name: str
    agentId: str
    agentName: str = ""
    status: str = "Pending"
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    duration: Optional[int] = None
    outputId: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaskCreateRequest(BaseModel):
    title: str
    content: str = ""
    agentId: str = ""


class MeetingMessageSchema(BaseModel):
    role: str = "agent"
    agentId: Optional[str] = None
    agentName: Optional[str] = None
    content: str
    timestamp: str


class MeetingRoundSchema(BaseModel):
    round: int
    name: str
    messages: list[MeetingMessageSchema] = Field(default_factory=list)


class MeetingOut(BaseModel):
    id: str
    topic: str
    agentIds: list[str] = Field(default_factory=list)
    status: str = "created"
    rounds: list[MeetingRoundSchema] = Field(default_factory=list)
    summary: Optional[str] = None
    decisions: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    createdAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MeetingCreateRequest(BaseModel):
    topic: str
    agentIds: list[str] = Field(..., min_length=2, max_length=10)


class MeetingMessageRequest(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    id: str
    agentId: str
    role: str
    content: str
    timestamp: str

    model_config = ConfigDict(from_attributes=True)


class ChatSendRequest(BaseModel):
    content: str


class OutputOut(BaseModel):
    id: str
    name: str
    type: str = "markdown"
    source: str = "task"
    content: Optional[str] = None
    url: Optional[str] = None
    createdAt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EventLogOut(BaseModel):
    id: str
    type: str = "system"
    title: str
    description: str = ""
    timestamp: str

    model_config = ConfigDict(from_attributes=True)


class WebhookPayload(BaseModel):
    event: str
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
