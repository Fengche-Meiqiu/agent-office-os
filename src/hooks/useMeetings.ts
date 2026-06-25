import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { meetingApi } from '@/lib/mockApi';

// 获取会议列表
export function useMeetings() {
  return useQuery({
    queryKey: ['meetings'],
    queryFn: () => meetingApi.getMeetings(),
  });
}

// 获取单个会议
export function useMeeting(id: string | undefined) {
  return useQuery({
    queryKey: ['meetings', id],
    queryFn: () => meetingApi.getMeeting(id!),
    enabled: !!id,
  });
}

// 创建会议
export function useCreateMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ topic, agentIds }: { topic: string; agentIds: string[] }) =>
      meetingApi.createMeeting(topic, agentIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['eventLogs'] });
    },
  });
}

// 主持人向当前轮次发送消息
export function useSendMeetingMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) =>
      meetingApi.sendMessage(id, content),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['meetings', id] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
    },
  });
}

// 会议进入下一轮
export function useNextRound() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => meetingApi.nextRound(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['meetings', id] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['outputs'] });
    },
  });
}

// 结束会议
export function useFinishMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => meetingApi.finishMeeting(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['meetings', id] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['outputs'] });
    },
  });
}
