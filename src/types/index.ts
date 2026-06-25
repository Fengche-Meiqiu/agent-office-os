// Agent 状态枚举
export type AgentStatus = 'ONLINE' | 'WORKING' | 'MEETING' | 'OFFLINE' | 'ERROR';

// 任务状态枚举
export type TaskStatus = 'Pending' | 'Running' | 'Completed' | 'Failed' | 'Cancelled';

// 平台类型
export type Platform = 'Hermes' | 'OpenClaw' | 'CrewAI' | 'LangGraph';

// 人才市场 Agent
export interface MarketplaceAgent {
  id: string;
  name: string;
  avatar: string;
  title: string;
  platform: Platform;
  skills: string[];
  tools: string[];
  status: 'ONLINE' | 'OFFLINE' | 'BUSY';
  description: string;
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

// 任务
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
}

// 会议消息
export interface MeetingMessage {
  role: 'user' | 'agent';
  agentId?: string;
  agentName?: string;
  content: string;
  timestamp: string;
}

// 会议轮次
export interface MeetingRound {
  round: number;
  name: string;
  messages: MeetingMessage[];
}

// 会议
export interface Meeting {
  id: string;
  topic: string;
  agentIds: string[];
  status: 'created' | 'running' | 'finished';
  rounds: MeetingRound[];
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
