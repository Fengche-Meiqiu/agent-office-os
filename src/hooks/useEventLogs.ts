import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eventLogApi } from '@/lib/mockApi';

// 获取系统事件日志
export function useEventLogs() {
  return useQuery({
    queryKey: ['eventLogs'],
    queryFn: () => eventLogApi.getLogs(),
  });
}

// 清空系统事件日志
export function useClearEventLogs() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => eventLogApi.clearLogs(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}
