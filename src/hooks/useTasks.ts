import { useQuery } from '@tanstack/react-query';
import { taskApi } from '@/lib/mockApi';

// 获取任务列表
export function useTasks() {
  return useQuery({
    queryKey: ['tasks'],
    queryFn: () => taskApi.getTasks(),
  });
}

// 获取单个任务
export function useTask(id: string | undefined) {
  return useQuery({
    queryKey: ['tasks', id],
    queryFn: () => taskApi.getTask(id!),
    enabled: !!id,
  });
}
