import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';

// 鑾峰彇鏌愪釜 Agent 鐨勮亰澶╄褰?
export function useChatMessages(agentId: string | undefined) {
  return useQuery({
    queryKey: ['chatMessages', agentId],
    queryFn: () => chatApi.getMessages(agentId!),
    enabled: !!agentId,
  });
}

// 鍙戦€佹秷鎭?
export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, content }: { agentId: string; content: string }) =>
      chatApi.sendMessage(agentId, content),
    onSuccess: (_, { agentId }) => {
      queryClient.invalidateQueries({ queryKey: ['chatMessages', agentId] });
      queryClient.invalidateQueries({ queryKey: ['officeAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}
