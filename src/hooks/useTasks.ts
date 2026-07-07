import { useQuery } from '@tanstack/react-query';
import { taskApi } from '@/lib/api';

// 鑾峰彇浠诲姟鍒楄〃
export function useTasks() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: () => taskApi.getTasks(),
  });
}

// 鑾峰彇鍗曚釜浠诲姟
export function useTask(id: string | undefined) {
  return useQuery({
    queryKey: ['tasks', id],
    queryFn: () => taskApi.getTask(id!),
    enabled: !!id,
  });
}
