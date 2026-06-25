import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { marketplaceApi, officeAgentApi } from '@/lib/mockApi';

// 获取人才市场 Agent 列表
export function useMarketplaceAgents() {
  return useQuery({
    queryKey: ['marketplaceAgents'],
    queryFn: () => marketplaceApi.getAgents(),
  });
}

// 雇佣 Agent
export function useHireAgent() {
  const queryClient = useQueryClient();
  return useMutation({
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
  return useQuery({
    queryKey: ['officeAgents'],
    queryFn: () => officeAgentApi.getAgents(),
  });
}

// 获取单个 Agent
export function useOfficeAgent(id: string | undefined) {
  return useQuery({
    queryKey: ['officeAgents', id],
    queryFn: () => officeAgentApi.getAgent(id!),
    enabled: !!id,
  });
}

// 解雇 Agent
export function useFireAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => officeAgentApi.fireAgent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['officeAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}
