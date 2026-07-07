import type { ChatMessage, EventLog, MarketplaceAgent, Meeting, OfficeAgent, Output, Task } from '@/types';
import { marketplaceAgents as seedMarketplaceAgents, officeAgents as seedOfficeAgents } from './mockData';

function generateId(prefix: string) {
  return `${prefix}_${Math.random().toString(16).slice(2, 10)}`;
}

class MockDB {
  private static instance: MockDB;
  private initialized = false;
  marketplaceAgents: MarketplaceAgent[] = [];
  officeAgents: OfficeAgent[] = [];
  tasks: Task[] = [];
  meetings: Meeting[] = [];
  outputs: Output[] = [];
  chatMessages: ChatMessage[] = [];
  eventLogs: EventLog[] = [];

  static getInstance() {
    if (!MockDB.instance) MockDB.instance = new MockDB();
    return MockDB.instance;
  }

  init() {
    if (this.initialized) return;
    this.marketplaceAgents = this.load('marketplaceAgents', seedMarketplaceAgents);
    this.officeAgents = this.load('officeAgents', seedOfficeAgents);
    this.tasks = this.load('tasks', []);
    this.meetings = this.load('meetings', []);
    this.outputs = this.load('outputs', []);
    this.chatMessages = this.load('chatMessages', []);
    this.eventLogs = this.load('eventLogs', []);
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

  persist() {
    localStorage.setItem('aagos_marketplaceAgents', JSON.stringify(this.marketplaceAgents));
    localStorage.setItem('aagos_officeAgents', JSON.stringify(this.officeAgents));
    localStorage.setItem('aagos_tasks', JSON.stringify(this.tasks));
    localStorage.setItem('aagos_meetings', JSON.stringify(this.meetings));
    localStorage.setItem('aagos_outputs', JSON.stringify(this.outputs));
    localStorage.setItem('aagos_chatMessages', JSON.stringify(this.chatMessages));
    localStorage.setItem('aagos_eventLogs', JSON.stringify(this.eventLogs));
  }

  reset() {
    ['marketplaceAgents', 'officeAgents', 'tasks', 'meetings', 'outputs', 'chatMessages', 'eventLogs'].forEach((key) => {
      localStorage.removeItem(`aagos_${key}`);
    });
    this.initialized = false;
    this.init();
  }
}

const db = MockDB.getInstance();
const delay = <T,>(value: T, ms = 120) => new Promise<T>((resolve) => setTimeout(() => resolve(value), ms));

export const marketplaceApi = {
  getAgents(): Promise<MarketplaceAgent[]> {
    db.init();
    return delay([...db.marketplaceAgents]);
  },
  syncAgents(): Promise<{ message: string; count: number }> {
    db.init();
    return delay({ message: 'mock sync completed', count: db.marketplaceAgents.length });
  },
  hireAgent(agentId: string): Promise<OfficeAgent> {
    db.init();
    const marketAgent = db.marketplaceAgents.find((agent) => agent.id === agentId);
    if (!marketAgent) throw new Error('Agent not found');
    const existing = db.officeAgents.find((agent) => agent.marketplaceId === agentId);
    if (existing) return delay(existing);

    const officeAgent: OfficeAgent = {
      id: generateId('office'),
      marketplaceId: marketAgent.id,
      name: marketAgent.name,
      avatar: marketAgent.avatar,
      title: marketAgent.title,
      platform: marketAgent.platform,
      platformAgentId: marketAgent.id,
      status: 'ONLINE',
      hiredAt: new Date().toISOString(),
      lastActiveAt: new Date().toISOString(),
      department: 'Unassigned',
      soul: {
        identity: marketAgent.title,
        goal: 'Complete user work reliably.',
        principles: 'Reliable, transparent, task-oriented.',
        style: 'Concise and professional.',
        description: marketAgent.description,
      },
      skills: [...marketAgent.skills],
      tools: [...marketAgent.tools],
      memory: [`Synced from ${marketAgent.platform}`],
      performance: { totalTasks: 0, successTasks: 0, failedTasks: 0, meetingCount: 0 },
    };
    db.officeAgents.push(officeAgent);
    db.eventLogs.unshift({
      id: generateId('event'),
      type: 'agent',
      title: `Agent hired: ${officeAgent.name}`,
      description: `Source: ${officeAgent.platform}`,
      timestamp: new Date().toISOString(),
    });
    db.persist();
    return delay(officeAgent);
  },
};

export const officeAgentApi = {
  getAgents(): Promise<OfficeAgent[]> {
    db.init();
    return delay([...db.officeAgents]);
  },
  getAgent(id: string): Promise<OfficeAgent | undefined> {
    db.init();
    return delay(db.officeAgents.find((agent) => agent.id === id));
  },
  fireAgent(id: string): Promise<void> {
    db.init();
    db.officeAgents = db.officeAgents.filter((agent) => agent.id !== id);
    db.persist();
    return delay(undefined);
  },
};

export const chatApi = {
  getMessages(agentId: string): Promise<ChatMessage[]> {
    db.init();
    return delay(db.chatMessages.filter((message) => message.agentId === agentId));
  },
  sendMessage(agentId: string, content: string): Promise<ChatMessage> {
    db.init();
    const userMsg: ChatMessage = { id: generateId('chat'), agentId, role: 'user', content, timestamp: new Date().toISOString() };
    db.chatMessages.push(userMsg);

    let reply = 'Received. I am processing your request.';
    if (content.trim().toLowerCase().startsWith('/task')) {
      const task: Task = {
        id: generateId('task'),
        name: content.replace(/^\/task/i, '').trim() || 'Agent task',
        agentId,
        agentName: db.officeAgents.find((agent) => agent.id === agentId)?.name || 'Agent',
        status: 'Completed',
        startedAt: new Date().toISOString(),
        endedAt: new Date().toISOString(),
        duration: 0,
        outputId: generateId('output'),
      };
      db.tasks.unshift(task);
      db.outputs.unshift({
        id: task.outputId!,
        name: `${task.name}.md`,
        type: 'markdown',
        source: 'task',
        content: `# ${task.name}\n\nMock task completed successfully.`,
        createdAt: new Date().toISOString(),
      });
      reply = `Task ${task.id} completed. Result has been saved to Outputs.`;
    }

    const agentReply: ChatMessage = { id: generateId('chat'), agentId, role: 'agent', content: reply, timestamp: new Date().toISOString() };
    db.chatMessages.push(agentReply);
    db.persist();
    return delay(agentReply);
  },
};

export const taskApi = {
  getTasks(): Promise<Task[]> {
    db.init();
    return delay([...db.tasks]);
  },
  getTask(id: string): Promise<Task | undefined> {
    db.init();
    return delay(db.tasks.find((task) => task.id === id));
  },
  createTask(data: { title: string; content: string; agentId: string }): Promise<Task> {
    db.init();
    const task: Task = {
      id: generateId('task'),
      name: data.title,
      agentId: data.agentId,
      agentName: db.officeAgents.find((agent) => agent.id === data.agentId)?.name || 'Agent',
      status: 'Completed',
      startedAt: new Date().toISOString(),
      endedAt: new Date().toISOString(),
      duration: 0,
      outputId: generateId('output'),
    };
    db.tasks.unshift(task);
    db.outputs.unshift({ id: task.outputId!, name: `${task.name}.md`, type: 'markdown', source: 'task', content: data.content, createdAt: new Date().toISOString() });
    db.persist();
    return delay(task);
  },
};

export const meetingApi = {
  getMeetings(): Promise<Meeting[]> {
    db.init();
    return delay([...db.meetings]);
  },
  getMeeting(id: string): Promise<Meeting | undefined> {
    db.init();
    return delay(db.meetings.find((meeting) => meeting.id === id));
  },
  createMeeting(topic: string, agentIds: string[]): Promise<Meeting> {
    db.init();
    const meeting: Meeting = { id: generateId('meeting'), topic, agentIds, status: 'created', rounds: [], createdAt: new Date().toISOString() };
    db.meetings.unshift(meeting);
    db.persist();
    return delay(meeting);
  },
  nextRound(id: string): Promise<Meeting | undefined> {
    db.init();
    const meeting = db.meetings.find((item) => item.id === id);
    if (!meeting) return delay(undefined);
    meeting.status = 'running';
    meeting.rounds.push({
      round: meeting.rounds.length + 1,
      name: 'Discussion',
      messages: meeting.agentIds.map((agentId) => ({
        role: 'agent',
        agentId,
        agentName: db.officeAgents.find((agent) => agent.id === agentId)?.name || 'Agent',
        content: 'Here is my view on this topic.',
        timestamp: new Date().toISOString(),
      })),
    });
    db.persist();
    return delay(meeting);
  },
  sendMessage(id: string, content: string): Promise<Meeting | undefined> {
    db.init();
    const meeting = db.meetings.find((item) => item.id === id);
    const round = meeting?.rounds[meeting.rounds.length - 1];
    if (round) round.messages.push({ role: 'user', content, timestamp: new Date().toISOString() });
    db.persist();
    return delay(meeting);
  },
  finishMeeting(id: string): Promise<Meeting | undefined> {
    db.init();
    const meeting = db.meetings.find((item) => item.id === id);
    if (!meeting) return delay(undefined);
    meeting.status = 'finished';
    meeting.summary = `Meeting finished: ${meeting.topic}`;
    const output: Output = {
      id: generateId('output'),
      name: `${meeting.topic} meeting notes.md`,
      type: 'markdown',
      source: 'meeting',
      content: `# ${meeting.topic}\n\n${meeting.summary}`,
      createdAt: new Date().toISOString(),
    };
    db.outputs.unshift(output);
    db.persist();
    return delay(meeting);
  },
};

export const outputApi = {
  getOutputs(): Promise<Output[]> {
    db.init();
    return delay([...db.outputs]);
  },
  getOutput(id: string): Promise<Output | undefined> {
    db.init();
    return delay(db.outputs.find((output) => output.id === id));
  },
};

export const eventLogApi = {
  getLogs(): Promise<EventLog[]> {
    db.init();
    return delay([...db.eventLogs]);
  },
  clearLogs(): Promise<void> {
    db.init();
    db.eventLogs = [];
    db.persist();
    return delay(undefined);
  },
};

export function resetMockData() {
  db.reset();
}
