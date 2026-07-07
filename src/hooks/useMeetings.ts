import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { meetingApi } from '@/lib/api';

// 鑾峰彇浼氳鍒楄〃
export function useMeetings() {
  return useQuery({
    queryKey: ['meetings'],
    queryFn: () => meetingApi.getMeetings(),
  });
}

// 鑾峰彇鍗曚釜浼氳
export function useMeeting(id: string | undefined) {
  return useQuery({
    queryKey: ['meetings', id],
    queryFn: () => meetingApi.getMeeting(id!),
    enabled: !!id,
  });
}

// 鍒涘缓浼氳
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

// 涓绘寔浜哄悜褰撳墠杞鍙戦€佹秷鎭?
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

// 浼氳杩涘叆涓嬩竴杞?
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

// 缁撴潫浼氳
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
