const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '');

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!resp.ok) {
    throw new Error(`API error: ${resp.status} ${resp.statusText}`);
  }

  if (resp.status === 204) {
    return undefined as T;
  }

  return resp.json();
}

export const marketplaceApi = {
  getAgents: () => request<any[]>('/api/marketplace/agents'),
  syncAgents: () => request<{ message: string; count: number }>('/api/marketplace/sync', { method: 'POST' }),
  hireAgent: (agentId: string) =>
    request<any>('/api/marketplace/hire', {
      method: 'POST',
      body: JSON.stringify({ agentId }),
    }),
};

export const officeAgentApi = {
  getAgents: () => request<any[]>('/api/office/agents'),
  getAgent: (id: string) => request<any>(`/api/office/agents/${id}`),
  fireAgent: (id: string) => request<void>(`/api/office/agents/${id}`, { method: 'DELETE' }),
};

export const chatApi = {
  getMessages: (agentId: string) => request<any[]>(`/api/chat/${agentId}/messages`),
  sendMessage: (agentId: string, content: string) =>
    request<any>(`/api/chat/${agentId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
};

export const taskApi = {
  getTasks: () => request<any[]>('/api/tasks'),
  createTask: (data: { title: string; content: string; agentId: string }) =>
    request<any>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getTask: (id: string) => request<any>(`/api/tasks/${id}`),
};

export const meetingApi = {
  getMeetings: () => request<any[]>('/api/meetings'),
  getMeeting: (id: string) => request<any>(`/api/meetings/${id}`),
  createMeeting: (topic: string, agentIds: string[]) =>
    request<any>('/api/meetings', {
      method: 'POST',
      body: JSON.stringify({ topic, agentIds }),
    }),
  nextRound: (id: string) => request<any>(`/api/meetings/${id}/next-round`, { method: 'POST' }),
  sendMessage: (id: string, content: string) =>
    request<any>(`/api/meetings/${id}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),
  finishMeeting: (id: string) => request<any>(`/api/meetings/${id}/finish`, { method: 'POST' }),
};

export const outputApi = {
  getOutputs: () => request<any[]>('/api/outputs'),
  getOutput: (id: string) => request<any>(`/api/outputs/${id}`),
};

export const eventLogApi = {
  getLogs: () => request<any[]>('/api/event-logs'),
  clearLogs: () => request<void>('/api/event-logs', { method: 'DELETE' }),
};
