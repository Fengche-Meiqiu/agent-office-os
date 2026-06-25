/**
 * 真实后端 API 客户端
 * 当 VITE_USE_MOCK=false 时，前端通过此文件调用后端真实接口
 *
 * 用法：
 *   开发时默认用 Mock（VITE_USE_MOCK=true 或不设置）
 *   部署时设置 VITE_USE_MOCK=false 切换到真实 API
 */

// 后端 API 基础地址，默认本机 8000 端口
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/**
 * 封装 fetch 请求，自动处理 JSON 和错误
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
    throw new Error(`API 错误: ${resp.status} ${resp.statusText}`);
  }

  // 处理无内容响应
  if (resp.status === 204) {
    return undefined as T;
  }

  return resp.json();
}

// ===== 人才市场 API =====
export const marketplaceApi = {
  /** 获取人才市场 Agent 列表 */
  getAgents: () => request<any[]>('/api/marketplace/agents'),

  /** 雇佣 Agent */
  hire: (agentId: string) =>
    request<{ officeAgentId: string }>('/api/marketplace/hire', {
      method: 'POST',
      body: JSON.stringify({ agentId }),
    }),
};

// ===== 办公室 Agent API =====
export const officeApi = {
  /** 获取所有已雇佣 Agent */
  getAgents: () => request<any[]>('/api/office/agents'),

  /** 获取单个 Agent 详情 */
  getAgent: (id: string) => request<any>(`/api/office/agents/${id}`),

  /** 解雇 Agent */
  fire: (id: string) =>
    request<void>(`/api/office/agents/${id}`, { method: 'DELETE' }),
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

  /** 创建任务 */
  createTask: (data: { title: string; content: string; agentId: string }) =>
    request<any>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** 获取单个任务 */
  getTask: (id: string) => request<any>(`/api/tasks/${id}`),
};

// ===== 会议 API =====
export const meetingApi = {
  /** 获取所有会议 */
  getMeetings: () => request<any[]>('/api/meetings'),

  /** 创建会议 */
  create: (data: { topic: string; agentIds: string[] }) =>
    request<any>('/api/meetings', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  /** 获取会议详情 */
  get: (id: string) => request<any>(`/api/meetings/${id}`),

  /** 进入下一轮 */
  nextRound: (id: string) =>
    request<any>(`/api/meetings/${id}/next-round`, { method: 'POST' }),

  /** 主持人插话 */
  sendMessage: (id: string, content: string) =>
    request<any>(`/api/meetings/${id}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  /** 结束会议 */
  finish: (id: string) =>
    request<any>(`/api/meetings/${id}/finish`, { method: 'POST' }),
};

// ===== 成果 API =====
export const outputApi = {
  /** 获取成果列表 */
  getOutputs: () => request<any[]>('/api/outputs'),

  /** 获取单个成果 */
  get: (id: string) => request<any>(`/api/outputs/${id}`),
};

// ===== 事件日志 API =====
export const eventLogApi = {
  /** 获取事件日志 */
  getLogs: () => request<any[]>('/api/event-logs'),

  /** 清空事件日志 */
  clearLogs: () =>
    request<void>('/api/event-logs', { method: 'DELETE' }),
};

// ===== 组织架构 API =====
export const organizationApi = {
  /** 获取组织架构（按部门分组） */
  get: () => request<any[]>('/api/organization'),
};
