/**
 * 真实后端 API 客户端（V2 重写）
 *
 * 方法名与 mockApi.ts 完全对齐，确保 api.ts 切换层无缝工作
 * V2 新增端点：
 * - marketplaceApi.sync() 主动同步人才市场
 * - meetingApi.start() / askAll() / askAgent() 自由讨论
 * - skillApi Skill 管理 CRUD
 * - SSE 实时推送端点
 */

// 后端 API 基础地址
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/**
 * 封装 fetch 请求，自动处理 JSON 和错误
 * 小白解释：所有 API 请求都走这个函数，它帮你把 JSON 转成对象，把错误抛出来
 */
async function request<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const resp = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!resp.ok) {
    // 尝试读取后端返回的错误详情
    let detail = '';
    try {
      const errBody = await resp.json();
      detail = errBody.detail || errBody.message || '';
    } catch {
      detail = resp.statusText;
    }
    throw new Error(`API 错误 ${resp.status}: ${detail}`);
  }

  if (resp.status === 204) {
    return undefined as T;
  }

  return resp.json();
}

// ===== 人才市场 API =====
export const marketplaceApi = {
  /** 获取人才市场 Agent 列表 */
  getAgents: () => request<any[]>('/api/marketplace/agents'),

  /** 主动从源平台同步 Agent（V2 新增） */
  sync: () =>
    request<{ message: string; added: string[]; updated: number; total: number }>(
      '/api/marketplace/sync',
      { method: 'POST' }
    ),

  /** 雇佣 Agent（方法名对齐 mockApi 的 hireAgent） */
  hireAgent: (agentId: string) =>
    request<{ message: string; agentId: string }>('/api/marketplace/hire', {
      method: 'POST',
      body: JSON.stringify({ agentId }),
    }),
};

// ===== 办公室 Agent API =====
// 注意：导出名为 officeAgentApi（对齐 mockApi）
export const officeAgentApi = {
  /** 获取所有已雇佣 Agent 列表（V2 返回精简版防 OOM） */
  getAgents: () => request<any[]>('/api/office/agents'),

  /** 获取单个 Agent 详情（完整版） */
  getAgent: (id: string) => request<any>(`/api/office/agents/${id}`),

  /** 解雇 Agent（方法名对齐 mockApi 的 fireAgent） */
  fireAgent: (id: string) =>
    request<{ message: string; agentId: string }>(`/api/office/agents/${id}`, {
      method: 'DELETE',
    }),
};

// ===== 聊天 API =====
export const chatApi = {
  /** 获取聊天记录 */
  getMessages: (agentId: string) =>
    request<any[]>(`/api/chat/${agentId}/messages`),

  /** 发送消息 */
  sendMessage: (agentId: string, content: string) =>
    request<any>(`/api/chat/${agentId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
};

// ===== 任务 API =====
export const taskApi = {
  /** 获取任务列表 */
  getTasks: () => request<any[]>('/api/tasks'),

  /** 创建任务（V2 新增 skillIds 参数） */
  createTask: (data: { title: string; content: string; agentId: string; skillIds?: string[] }) =>
    request<any>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** 获取单个任务 */
  getTask: (id: string) => request<any>(`/api/tasks/${id}`),

  /** 获取任务执行日志（V2 新增） */
  getTaskLogs: (id: string) => request<any[]>(`/api/tasks/${id}/logs`),
};

// ===== 会议 API（V2 重构：自由讨论） =====
export const meetingApi = {
  /** 获取所有会议 */
  getMeetings: () => request<any[]>('/api/meetings'),

  /** 获取单个会议（方法名对齐 mockApi 的 getMeeting） */
  getMeeting: (id: string) => request<any>(`/api/meetings/${id}`),

  /** 创建会议（方法名对齐 mockApi 的 createMeeting） */
  createMeeting: (topic: string, agentIds: string[]) =>
    request<any>('/api/meetings', {
      method: 'POST',
      body: JSON.stringify({ topic, agentIds }),
    }),

  /** 开始会议：所有参会 Agent 首次发言（V2 新增） */
  start: (id: string) =>
    request<any>(`/api/meetings/${id}/start`, { method: 'POST' }),

  /** 让所有 Agent 发言（V2 新增） */
  askAll: (id: string) =>
    request<any>(`/api/meetings/${id}/ask-all`, { method: 'POST' }),

  /** 让指定 Agent 发言（V2 新增） */
  askAgent: (meetingId: string, agentId: string) =>
    request<any>(`/api/meetings/${meetingId}/ask/${agentId}`, { method: 'POST' }),

  /** 主持人插话 */
  sendMessage: (id: string, content: string) =>
    request<any>(`/api/meetings/${id}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  /** 结束会议（方法名对齐 mockApi 的 finishMeeting） */
  finishMeeting: (id: string) =>
    request<any>(`/api/meetings/${id}/finish`, { method: 'POST' }),
};

// ===== Skill 管理 API（V2 新增） =====
export const skillApi = {
  /** 获取平台级 Skill 目录 */
  listSkills: () => request<any[]>('/api/skills'),

  /** 获取单个 Skill 详情 */
  getSkill: (skillId: string) => request<any>(`/api/skills/${skillId}`),

  /** 获取 Agent 的技能列表 */
  listAgentSkills: (agentId: string) =>
    request<any[]>(`/api/agents/${agentId}/skills`),

  /** 给 Agent 添加 Skill */
  addAgentSkill: (agentId: string, skillId: string, params: object = {}) =>
    request<any>(`/api/agents/${agentId}/skills`, {
      method: 'POST',
      body: JSON.stringify({ skillId, params }),
    }),

  /** 修改 Agent 的 Skill 配置（启停/改参数） */
  updateAgentSkill: (agentId: string, skillId: string, data: { enabled?: boolean; params?: object }) =>
    request<any>(`/api/agents/${agentId}/skills/${skillId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  /** 移除 Agent 的 Skill */
  removeAgentSkill: (agentId: string, skillId: string) =>
    request<{ message: string }>(`/api/agents/${agentId}/skills/${skillId}`, {
      method: 'DELETE',
    }),

  /** 从源平台刷新 Agent 技能 */
  refreshAgentSkills: (agentId: string) =>
    request<{ message: string; added: string[]; totalRemote: number }>(
      `/api/agents/${agentId}/skills/refresh`,
      { method: 'POST' }
    ),
};

// ===== 成果 API =====
export const outputApi = {
  /** 获取成果列表 */
  getOutputs: () => request<any[]>('/api/outputs'),

  /** 获取单个成果（方法名对齐 mockApi 的 getOutput） */
  getOutput: (id: string) => request<any>(`/api/outputs/${id}`),
};

// ===== 事件日志 API =====
export const eventLogApi = {
  /** 获取事件日志 */
  getLogs: () => request<any[]>('/api/event-logs'),

  /** 清空事件日志 */
  clearLogs: () =>
    request<void>('/api/event-logs', { method: 'DELETE' }),
};

// ===== SSE 实时推送（V2 新增） =====
/**
 * 创建 SSE 连接，订阅后端事件
 * 小白解释：开一条"实时通道"，后端有新消息会自动推过来，不用反复刷新
 *
 * @param channel 订阅通道：'tasks' 或 'meetings'
 * @param handlers 事件处理函数映射
 * @returns cleanup 函数，调用后关闭连接
 */
export function createSSEConnection(
  channel: 'tasks' | 'meetings',
  handlers: Record<string, (data: any) => void>
): () => void {
  const eventSource = new EventSource(`${API_BASE}/api/sse/${channel}`);

  // 连接成功
  eventSource.addEventListener('connected', (e) => {
    console.log(`[SSE] ${channel} 已连接`);
  });

  // 注册所有事件处理器
  for (const [eventType, handler] of Object.entries(handlers)) {
    eventSource.addEventListener(eventType, (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        handler(data);
      } catch (err) {
        console.error(`[SSE] 解析事件 ${eventType} 失败:`, err);
      }
    });
  }

  eventSource.onerror = () => {
    console.warn(`[SSE] ${channel} 连接异常，将自动重连`);
  };

  // 返回清理函数
  return () => {
    eventSource.close();
    console.log(`[SSE] ${channel} 已断开`);
  };
}
