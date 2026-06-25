import type {
  MarketplaceAgent,
  OfficeAgent,
  Task,
  Meeting,
  Output,
  ChatMessage,
  EventLog,
} from '@/types';
import {
  marketplaceAgents,
  officeAgents,
  tasks,
  meetings,
  outputs,
  chatMessages,
  eventLogs,
  generateId,
} from './mockData';

// MockDB 类：用 LocalStorage 模拟数据库
class MockDB {
  private static instance: MockDB;
  private initialized = false;

  // 内存中的数据表
  marketplaceAgents: MarketplaceAgent[] = [];
  officeAgents: OfficeAgent[] = [];
  tasks: Task[] = [];
  meetings: Meeting[] = [];
  outputs: Output[] = [];
  chatMessages: ChatMessage[] = [];
  eventLogs: EventLog[] = [];

  private constructor() {}

  static getInstance(): MockDB {
    if (!MockDB.instance) {
      MockDB.instance = new MockDB();
    }
    return MockDB.instance;
  }

  // 初始化数据：优先从 LocalStorage 读取，否则使用种子数据
  init() {
    if (this.initialized) return;

    this.marketplaceAgents = this.load('marketplaceAgents', marketplaceAgents);
    this.officeAgents = this.load('officeAgents', officeAgents);
    this.tasks = this.load('tasks', tasks);
    this.meetings = this.load('meetings', meetings);
    this.outputs = this.load('outputs', outputs);
    this.chatMessages = this.load('chatMessages', chatMessages);
    this.eventLogs = this.load('eventLogs', eventLogs);

    this.initialized = true;
  }

  private load<T>(key: string, fallback: T[]): T[] {
    try {
      const raw = localStorage.getItem(`aagos_${key}`);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  }

  private save(key: string, data: unknown) {
    localStorage.setItem(`aagos_${key}`, JSON.stringify(data));
  }

  persist() {
    this.save('marketplaceAgents', this.marketplaceAgents);
    this.save('officeAgents', this.officeAgents);
    this.save('tasks', this.tasks);
    this.save('meetings', this.meetings);
    this.save('outputs', this.outputs);
    this.save('chatMessages', this.chatMessages);
    this.save('eventLogs', this.eventLogs);
  }

  reset() {
    localStorage.removeItem('aagos_marketplaceAgents');
    localStorage.removeItem('aagos_officeAgents');
    localStorage.removeItem('aagos_tasks');
    localStorage.removeItem('aagos_meetings');
    localStorage.removeItem('aagos_outputs');
    localStorage.removeItem('aagos_chatMessages');
    localStorage.removeItem('aagos_eventLogs');
    this.initialized = false;
    this.init();
  }
}

const db = MockDB.getInstance();

// 模拟网络延迟
function delay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

// 人才市场 API
export const marketplaceApi = {
  getAgents(): Promise<MarketplaceAgent[]> {
    db.init();
    return delay([...db.marketplaceAgents]);
  },

  hireAgent(agentId: string): Promise<OfficeAgent> {
    db.init();
    const marketAgent = db.marketplaceAgents.find((a) => a.id === agentId);
    if (!marketAgent) throw new Error('Agent not found');

    const existing = db.officeAgents.find((a) => a.marketplaceId === agentId);
    if (existing) throw new Error('Agent already hired');

    const officeAgent: OfficeAgent = {
      id: generateId('office'),
      marketplaceId: marketAgent.id,
      name: marketAgent.name,
      avatar: marketAgent.avatar,
      title: marketAgent.title,
      platform: marketAgent.platform,
      platformAgentId: `platform_${marketAgent.id}`,
      status: 'ONLINE',
      hiredAt: new Date().toISOString(),
      lastActiveAt: new Date().toISOString(),
      department: '未分配',
      managerId: 'ceo',
      soul: {
        identity: `${marketAgent.title}`,
        goal: '为用户提供专业服务',
        principles: '专业、可靠、高效',
        style: '稳定、专注',
        description: marketAgent.description,
      },
      skills: [...marketAgent.skills],
      tools: [...marketAgent.tools],
      memory: [`来自 ${marketAgent.platform} 平台`, `擅长 ${marketAgent.skills.join('、')}`],
      performance: { totalTasks: 0, successTasks: 0, failedTasks: 0, meetingCount: 0 },
    };

    db.officeAgents.push(officeAgent);
    db.eventLogs.unshift({
      id: generateId('event'),
      type: 'agent',
      title: `${officeAgent.name} 加入办公室`,
      description: '刚被雇佣',
      timestamp: new Date().toISOString(),
    });
    db.persist();
    return delay(officeAgent);
  },
};

// 办公室 Agent API
export const officeAgentApi = {
  getAgents(): Promise<OfficeAgent[]> {
    db.init();
    return delay([...db.officeAgents]);
  },

  getAgent(id: string): Promise<OfficeAgent | undefined> {
    db.init();
    return delay(db.officeAgents.find((a) => a.id === id));
  },

  fireAgent(id: string): Promise<void> {
    db.init();
    db.officeAgents = db.officeAgents.filter((a) => a.id !== id);
    db.eventLogs.unshift({
      id: generateId('event'),
      type: 'agent',
      title: `Agent 已被解雇`,
      description: id,
      timestamp: new Date().toISOString(),
    });
    db.persist();
    return delay(undefined);
  },
};

// 任务 API
export const taskApi = {
  getTasks(): Promise<Task[]> {
    db.init();
    return delay([...db.tasks]);
  },

  getTask(id: string): Promise<Task | undefined> {
    db.init();
    return delay(db.tasks.find((t) => t.id === id));
  },
};

// 会议 API
export const meetingApi = {
  getMeetings(): Promise<Meeting[]> {
    db.init();
    return delay([...db.meetings]);
  },

  getMeeting(id: string): Promise<Meeting | undefined> {
    db.init();
    return delay(db.meetings.find((m) => m.id === id));
  },

  createMeeting(topic: string, agentIds: string[]): Promise<Meeting> {
    db.init();
    const meeting: Meeting = {
      id: generateId('meeting'),
      topic,
      agentIds,
      status: 'created',
      rounds: [],
      createdAt: new Date().toISOString(),
    };
    db.meetings.push(meeting);
    db.eventLogs.unshift({
      id: generateId('event'),
      type: 'meeting',
      title: `创建会议室"${topic}"`,
      description: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      timestamp: new Date().toISOString(),
    });
    db.persist();
    return delay(meeting);
  },

  nextRound(id: string): Promise<Meeting | undefined> {
    db.init();
    const meeting = db.meetings.find((m) => m.id === id);
    if (!meeting) return delay(undefined);

    const roundNames = ['独立意见', '交叉评论', '达成共识', '形成结论'];
    const nextRoundNumber = meeting.rounds.length + 1;

    if (nextRoundNumber > 4) {
      meeting.status = 'finished';
      meeting.summary = `关于"${meeting.topic}"的讨论已结束，形成了明确的决策与行动项。`;
      meeting.decisions = ['决策一：继续推进当前方向', '决策二：加强跨部门协作'];
      meeting.actions = ['整理会议纪要', '分配后续任务', '跟进执行情况'];
      generateMeetingOutput(meeting);
    } else {
      meeting.status = 'running';
      meeting.rounds.push({
        round: nextRoundNumber,
        name: roundNames[nextRoundNumber - 1],
        messages: meeting.agentIds.map((agentId) => {
          const agent = db.officeAgents.find((a) => a.id === agentId);
          return {
            role: 'agent' as const,
            agentId,
            agentName: agent?.name || 'Unknown',
            content: `这是我在${roundNames[nextRoundNumber - 1]}阶段的观点。`,
            timestamp: new Date().toISOString(),
          };
        }),
      });
    }

    db.persist();
    return delay(meeting);
  },

  sendMessage(id: string, content: string): Promise<Meeting | undefined> {
    db.init();
    const meeting = db.meetings.find((m) => m.id === id);
    if (!meeting) return delay(undefined);

    const currentRound = meeting.rounds[meeting.rounds.length - 1];
    if (!currentRound || meeting.status === 'finished') return delay(meeting);

    currentRound.messages.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    });

    db.persist();
    return delay(meeting);
  },

  finishMeeting(id: string): Promise<Meeting | undefined> {
    db.init();
    const meeting = db.meetings.find((m) => m.id === id);
    if (!meeting) return delay(undefined);

    meeting.status = 'finished';
    meeting.summary = `关于"${meeting.topic}"的讨论已结束，形成了明确的决策与行动项。`;
    meeting.decisions = ['决策一：继续推进当前方向', '决策二：加强跨部门协作'];
    meeting.actions = ['整理会议纪要', '分配后续任务', '跟进执行情况'];

    // 自动生成会议纪要并归档到成果中心
    generateMeetingOutput(meeting);

    db.persist();
    return delay(meeting);
  },
};

/**
 * 根据会议内容生成 Markdown 会议纪要，并存入成果中心
 */
function generateMeetingOutput(meeting: Meeting) {
  const participantNames = meeting.agentIds
    .map((id) => db.officeAgents.find((a) => a.id === id)?.name || 'Unknown')
    .join('、');

  const roundSummaries = meeting.rounds
    .map((round) => {
      const lines = round.messages
        .map((msg) => {
          if (msg.role === 'user') return `- 主持人：${msg.content}`;
          return `- ${msg.agentName}：${msg.content}`;
        })
        .join('\n');
      return `### Round ${round.round} ${round.name}\n\n${lines}`;
    })
    .join('\n\n');

  const decisions = meeting.decisions?.map((d) => `- ${d}`).join('\n') || '';
  const actions = meeting.actions?.map((a) => `- ${a}`).join('\n') || '';

  const content = `# ${meeting.topic} 会议纪要\n\n## 参会人\n\n${participantNames}\n\n## 讨论摘要\n\n${roundSummaries}\n\n## 决策\n\n${decisions}\n\n## 行动项\n\n${actions}`;

  const output: Output = {
    id: generateId('output'),
    name: `${meeting.topic}会议纪要.md`,
    type: 'markdown',
    source: 'meeting',
    content,
    createdAt: new Date().toISOString(),
  };

  db.outputs.unshift(output);
}

// 成果 API
export const outputApi = {
  getOutputs(): Promise<Output[]> {
    db.init();
    return delay([...db.outputs]);
  },

  getOutput(id: string): Promise<Output | undefined> {
    db.init();
    return delay(db.outputs.find((o) => o.id === id));
  },
};

// 聊天 API
export const chatApi = {
  getMessages(agentId: string): Promise<ChatMessage[]> {
    db.init();
    return delay(db.chatMessages.filter((m) => m.agentId === agentId).sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    ));
  },

  sendMessage(agentId: string, content: string): Promise<ChatMessage> {
    db.init();
    const userMsg: ChatMessage = {
      id: generateId('chat'),
      agentId,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    db.chatMessages.push(userMsg);

    const agentReply: ChatMessage = {
      id: generateId('chat'),
      agentId,
      role: 'agent',
      content: '收到，我正在处理您的请求，请稍等。',
      timestamp: new Date().toISOString(),
    };
    db.chatMessages.push(agentReply);

    const agent = db.officeAgents.find((a) => a.id === agentId);
    if (agent) {
      agent.lastActiveAt = new Date().toISOString();
    }

    db.persist();
    return delay(agentReply);
  },
};

// 事件日志 API
export const eventLogApi = {
  getLogs(): Promise<EventLog[]> {
    db.init();
    return delay([...db.eventLogs].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    ));
  },

  clearLogs(): Promise<void> {
    db.init();
    db.eventLogs = [];
    db.persist();
    return delay(undefined);
  },
};

// 重置数据（开发调试用）
export function resetMockData() {
  db.reset();
}
