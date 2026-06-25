import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '@/lib/mockApi';

// 获取某个 Agent 的聊天记录
export function useChatMessages(agentId: string | undefined) {
  return useQuery({
    queryKey: ['chatMessages', agentId],
    queryFn: () => chatApi.getMessages(agentId!),
    enabled: !!agentId,
  });
}

// 发送消息
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
