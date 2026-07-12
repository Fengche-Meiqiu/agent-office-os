import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatApi } from '@/lib/api';

// 获取某个 Agent 的聊天记录
export function useChatMessages(agentId: string | undefined) {
  return useQuery({
    queryKey: ['chatMessages', agentId],
    queryFn: () => chatApi.getMessages(agentId!),
    enabled: !!agentId,
  });
}

// 发送消息（带乐观更新：用户消息立即显示，不等 Agent 回复）
export function useSendMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, content }: { agentId: string; content: string }) =>
      chatApi.sendMessage(agentId, content),
    onMutate: async ({ agentId, content }) => {
      // 取消正在进行的 refetch，避免覆盖乐观更新
      await queryClient.cancelQueries({ queryKey: ['chatMessages', agentId] });

      // 获取当前缓存
      const previous = queryClient.getQueryData(['chatMessages', agentId]);

      // 构造临时用户消息
      const tempMsg = {
        id: `temp_${Date.now()}`,
        agentId,
        role: 'user' as const,
        content,
        timestamp: new Date().toISOString(),
      };

      // 乐观插入到缓存
      queryClient.setQueryData(['chatMessages', agentId], (old: any[]) => {
        return [...(old || []), tempMsg];
      });

      // 返回回滚函数需要的上下文
      return { agentId, previous };
    },
    onError: (err, { agentId, content }, context) => {
      // 失败时还原缓存
      if (context?.previous) {
        queryClient.setQueryData(['chatMessages', agentId], context.previous);
      }

      // 小白解释：聊天接口失败时，给用户明确的提示。
      // 如果是超时，建议改用 /task 异步任务模式，因为分析类请求耗时太长。
      const msg = err instanceof Error ? err.message : '未知错误';
      if (msg.includes('超时') || msg.includes('timeout') || msg.includes('120')) {
        alert(
          `消息发送失败：${msg}\n\n分析类问题耗时可能超过 120 秒，建议改用任务模式：\n/task ${content}`
        );
      } else {
        alert(`消息发送失败：${msg}`);
      }
    },
    onSettled: (_, __, { agentId }) => {
      // 无论成功失败，最终重新拉取保证一致性
      queryClient.invalidateQueries({ queryKey: ['chatMessages', agentId] });
      queryClient.invalidateQueries({ queryKey: ['officeAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}
