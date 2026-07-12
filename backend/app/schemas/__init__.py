"""
Pydantic Schemas（V2）
新增：Skill/AgentSkill/TaskLog schema
变更：TaskOut 扩展 result/progress/currentStep/skillIds；Meeting 的 rounds 改为 messages
WebhookPayload 扩展 task_progress/task_step 事件字段
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class SoulSchema(BaseModel):
    """Agent 人格（Soul）数据"""
    identity: str = ""
    goal: str = ""
    principles: str = ""
    style: str = ""
    description: str = ""


# ===== 人才市场 =====
class MarketplaceAgentOut(BaseModel):
    """人才市场 Agent 响应模型"""
    id: str
    name: str
    avatar: str = ""
    title: str = ""
    platform: str = "hermes"
    platformAgentId: str = ""
    skills: list[str] = []
    tools: list[str] = []
    status: str = "ONLINE"
    description: str = ""
    soul: SoulSchema = SoulSchema()

    class Config:
        from_attributes = True


# ===== 办公室 Agent =====
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
    platform: str = "hermes"
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


class OfficeAgentListOut(BaseModel):
    """办公室 Agent 列表项（精简版，不含 skills/memory/performance，保留 tools 避免工具中心崩溃）"""
    id: str
    marketplaceId: str = ""
    name: str
    avatar: str = ""
    title: str = ""
    platform: str = "hermes"
    platformAgentId: str = ""
    status: str = "ONLINE"
    department: str = "未分配"
    tools: list[str] = []
    hiredAt: Optional[str] = None
    lastActiveAt: Optional[str] = None

    class Config:
        from_attributes = True


class HireRequest(BaseModel):
    """雇佣 Agent 请求"""
    agentId: str = Field(..., description="人才市场 Agent ID")


# ===== Skill 管理（V2 新增）=====
class SkillOut(BaseModel):
    """技能目录响应"""
    id: str
    name: str
    description: str = ""
    paramsSchema: dict = {}
    requiredTools: list[str] = []
    sourcePlatform: str = "hermes"
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True


class AgentSkillOut(BaseModel):
    """Agent 技能关联响应（含启用状态/参数/使用统计）"""
    id: str
    agentId: str
    skillId: str
    skillName: str = ""
    skillDescription: str = ""
    enabled: bool = True
    params: dict = {}
    lastUsedAt: Optional[str] = None
    useCount: int = 0

    class Config:
        from_attributes = True


class AgentSkillAddRequest(BaseModel):
    """给 Agent 添加技能"""
    skillId: str
    params: dict = {}


class AgentSkillUpdateRequest(BaseModel):
    """修改 Agent 技能（启停/改参数）"""
    enabled: Optional[bool] = None
    params: Optional[dict] = None


# ===== 任务 =====
class TaskOut(BaseModel):
    """任务响应模型（V2 扩展）"""
    id: str
    name: str
    agentId: str
    agentName: str = ""
    status: str = "Pending"
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    duration: Optional[int] = None
    outputId: Optional[str] = None
    # V2 新增
    result: Optional[str] = None
    progress: int = 0
    currentStep: Optional[str] = None
    skillIds: list[str] = []
    platformTaskId: Optional[str] = None  # 源平台返回的任务 ID

    class Config:
        from_attributes = True


class TaskCreateRequest(BaseModel):
    """创建任务请求（V2 新增 skillIds）"""
    title: str
    content: str = ""
    agentId: str = ""
    skillIds: list[str] = []


# ===== TaskLog（V2 新增）=====
class TaskLogOut(BaseModel):
    """任务执行日志响应"""
    id: str
    taskId: str
    step: str = ""
    detail: str = ""
    level: str = "info"
    timestamp: str

    class Config:
        from_attributes = True


# ===== 会议（V2 重构：rounds → messages）=====
class MeetingMessageSchema(BaseModel):
    """会议消息"""
    role: str = "agent"  # user / agent
    agentId: Optional[str] = None
    agentName: Optional[str] = None
    content: str
    timestamp: str


class MeetingOut(BaseModel):
    """会议响应模型（V2：messages 替代 rounds）"""
    id: str
    topic: str
    agentIds: list[str] = []
    status: str = "created"
    messages: list[MeetingMessageSchema] = []
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
    # 小白解释：Hermes 建议这条回复用 /task 模式时返回 true
    suggestTask: bool = False
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


# ===== Webhook（V2 扩展）=====
class WebhookPayload(BaseModel):
    """
    Hermes Webhook 回调数据
    V2 新增事件：task_progress（进度更新）、task_step（步骤日志）
    V2 新增字段：progress、step、detail
    """
    event: str  # task_created / task_started / task_completed / task_failed / task_progress / task_step / agent_online / agent_offline
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
    # V2 新增
    progress: Optional[int] = None  # 0-100
    step: Optional[str] = None  # 步骤名
    detail: Optional[str] = None  # 步骤详情
