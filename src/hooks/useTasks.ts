import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { taskApi } from '@/lib/api';

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

// 创建任务（从聊天或会议室的 /task 指令触发）
// 小白解释：这个 hook 用来"布置正式任务"。
// 成功后会自动刷新任务列表、员工列表和事件日志，让用户在任务中心看到新任务。
export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { title: string; content: string; agentId: string; skillIds?: string[] }) =>
      taskApi.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['officeAgents'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
    onError: (err) => {
      // 小白解释：这里不弹 alert，把错误处理交给调用方（比如 Chat.tsx 显示页面内提示）。
      // 如果 hook 调用方没处理，错误会在 console 里打印。
      console.error('[useCreateTask] 任务创建失败：', err);
    },
  });
}
