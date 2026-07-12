import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { meetingApi } from '@/lib/api';

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

// 主持人插话
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

// V2 新增：开始会议（所有 Agent 首次发言）
export function useStartMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => meetingApi.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['meetings', id] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
    },
  });
}

// V2 新增：让所有 Agent 发言
export function useAskAll() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => meetingApi.askAll(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['meetings', id] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
    },
  });
}

// V2 新增：让指定 Agent 发言
export function useAskAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ meetingId, agentId }: { meetingId: string; agentId: string }) =>
      meetingApi.askAgent(meetingId, agentId),
    onSuccess: (_, { meetingId }) => {
      queryClient.invalidateQueries({ queryKey: ['meetings', meetingId] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
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
