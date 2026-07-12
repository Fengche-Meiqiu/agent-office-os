import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { marketplaceApi, officeAgentApi } from '@/lib/api';
import type { OfficeAgent } from '@/types';

// 获取人才市场 Agent 列表
export function useMarketplaceAgents() {
  return useQuery({
    queryKey: ['marketplaceAgents'],
    queryFn: () => marketplaceApi.getAgents(),
  });
}

// 从源平台同步人才市场 Agent
// 小白解释：点一下"刷新人才库"，从 Hermes 等平台把最新 Agent 拉到本地。
export function useSyncMarketplace() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string; added: string[]; updated: number; total: number }, Error>({
    mutationFn: () => marketplaceApi.sync(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplaceAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
    onError: (err) => {
      const msg = err instanceof Error ? err.message : '未知错误';
      alert(`人才市场同步失败：${msg}`);
    },
  });
}

// 雇佣 Agent
// 小白解释：这个 hook 用来"雇佣"人才市场的 Agent。
// 成功后会自动刷新人才市场列表、办公室 Agent 列表和事件日志。
export function useHireAgent() {
  const queryClient = useQueryClient();
  return useMutation<{ agentId: string; message: string }, Error, string>({
    mutationFn: (agentId: string) => marketplaceApi.hireAgent(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplaceAgents'] });
      queryClient.invalidateQueries({ queryKey: ['officeAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}

// 获取已雇佣 Agent 列表
export function useOfficeAgents() {
  return useQuery<OfficeAgent[]>({
    queryKey: ['officeAgents'],
    queryFn: () => officeAgentApi.getAgents(),
  });
}

// 获取单个 Agent
export function useOfficeAgent(id: string | undefined) {
  return useQuery<OfficeAgent>({
    queryKey: ['officeAgents', id],
    queryFn: () => officeAgentApi.getAgent(id!),
    enabled: !!id,
  });
}

// 解雇 Agent
// 小白解释：这个 hook 用来"解雇"已雇佣的 Agent。
// 成功后会先删掉当前 Agent 的详情缓存，再刷新列表，避免页面跳转前闪现"未找到该员工"。
export function useFireAgent() {
  const queryClient = useQueryClient();
  return useMutation<{ agentId: string; message: string }, Error, string>({
    mutationFn: (id: string) => officeAgentApi.fireAgent(id),
    onSuccess: (_, id) => {
      // 先移除当前 Agent 的详情缓存，避免跳转到首页前闪现"未找到该员工"
      queryClient.removeQueries({ queryKey: ['officeAgents', id] });
      queryClient.invalidateQueries({ queryKey: ['officeAgents'] });
      queryClient.invalidateQueries({ queryKey: ['marketplaceAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}
