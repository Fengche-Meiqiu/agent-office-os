// Agent 状态枚举
export type AgentStatus = 'ONLINE' | 'WORKING' | 'MEETING' | 'OFFLINE' | 'ERROR';

// 任务状态枚举
export type TaskStatus = 'Pending' | 'Running' | 'Completed' | 'Failed' | 'Cancelled';

// 平台类型
export type Platform = 'Hermes';

// 人才市场 Agent
export interface MarketplaceAgent {
  id: string;
  name: string;
  avatar: string;
  title: string;
  platform: Platform;
  platformAgentId: string;
  skills: string[];
  tools: string[];
  status: 'ONLINE' | 'OFFLINE' | 'BUSY';
  description: string;
  soul: AgentSoul;
}

// Soul 人格
export interface AgentSoul {
  identity: string;
  goal: string;
  principles: string;
  style: string;
  description: string;
}

// 绩效
export interface AgentPerformance {
  totalTasks: number;
  successTasks: number;
  failedTasks: number;
  meetingCount: number;
}

// 已雇佣 Agent
export interface OfficeAgent {
  id: string;
  marketplaceId: string;
  name: string;
  avatar: string;
  title: string;
  platform: Platform;
  platformAgentId: string;
  status: AgentStatus;
  hiredAt: string;
  lastActiveAt: string;
  department?: string;
  managerId?: string;
  soul: AgentSoul;
  skills: string[];
  tools: string[];
  memory: string[];
  performance: AgentPerformance;
}

// 任务（V2 扩展：result/progress/currentStep/skillIds）
export interface Task {
  id: string;
  name: string;
  agentId: string;
  agentName: string;
  status: TaskStatus;
  startedAt?: string;
  endedAt?: string;
  duration?: number;
  outputId?: string;
  // V2 新增
  result?: string;
  progress?: number;
  currentStep?: string;
  skillIds?: string[];
}

// 会议消息
// 小白解释：会议里的一条发言，可以是 Agent 说的，也可以是主持人（用户）说的。
// round / roundName 是可选的，用来标记这条消息属于第几轮讨论。
export interface MeetingMessage {
  role: 'user' | 'agent';
  agentId?: string;
  agentName?: string;
  content: string;
  timestamp: string;
  round?: number;
  roundName?: string;
}

// 会议（V2 重构：rounds → messages 扁平列表）
export interface Meeting {
  id: string;
  topic: string;
  agentIds: string[];
  status: 'created' | 'running' | 'finished';
  messages: MeetingMessage[];
  summary?: string;
  decisions?: string[];
  actions?: string[];
  createdAt: string;
}

// 成果
export interface Output {
  id: string;
  name: string;
  type: 'markdown' | 'pdf' | 'html' | 'image' | 'link';
  source: 'task' | 'meeting' | 'upload';
  content?: string;
  url?: string;
  createdAt: string;
}

// 聊天消息
export interface ChatMessage {
  id: string;
  agentId: string;
  role: 'user' | 'agent';
  content: string;
  // 小白解释：Hermes 返回 true 时，表示这条回复建议改用 /task 任务模式
  suggestTask?: boolean;
  timestamp: string;
}

// 系统事件
export interface EventLog {
  id: string;
  type: 'task' | 'meeting' | 'system' | 'agent';
  title: string;
  description: string;
  timestamp: string;
}

// 应用导航项
export interface NavItem {
  label: string;
  path: string;
  icon: string;
}
