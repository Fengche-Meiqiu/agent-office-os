import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eventLogApi } from '@/lib/api';

// 鑾峰彇绯荤粺浜嬩欢鏃ュ織
export function useEventLogs() {
  return useQuery({
    queryKey: ['eventLogs'],
    queryFn: () => eventLogApi.getLogs(),
  });
}

// 娓呯┖绯荤粺浜嬩欢鏃ュ織
export function useClearEventLogs() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => eventLogApi.clearLogs(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}
