import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { marketplaceApi, officeAgentApi } from '@/lib/api';

// 鑾峰彇浜烘墠甯傚満 Agent 鍒楄〃
export function useMarketplaceAgents() {
  return useQuery({
    queryKey: ['marketplaceAgents'],
    queryFn: () => marketplaceApi.getAgents(),
  });
}

// 闆囦剑 Agent
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

// 鑾峰彇宸查泧浣?Agent 鍒楄〃
export function useOfficeAgents() {
  return useQuery({
    queryKey: ['officeAgents'],
    queryFn: () => officeAgentApi.getAgents(),
  });
}

// 鑾峰彇鍗曚釜 Agent
export function useOfficeAgent(id: string | undefined) {
  return useQuery({
    queryKey: ['officeAgents', id],
    queryFn: () => officeAgentApi.getAgent(id!),
    enabled: !!id,
  });
}

// 瑙ｉ泧 Agent
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


export function useSyncMarketplaceAgents() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => marketplaceApi.syncAgents?.() ?? Promise.resolve({ message: 'mock sync skipped', count: 0 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplaceAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}
