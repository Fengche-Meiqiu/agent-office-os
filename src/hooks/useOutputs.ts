import { useQuery } from '@tanstack/react-query';
import { outputApi } from '@/lib/mockApi';

// 获取成果列表
export function useOutputs() {
  return useQuery({
    queryKey: ['outputs'],
    queryFn: () => outputApi.getOutputs(),
  });
}

// 获取单个成果
export function useOutput(id: string | undefined) {
  return useQuery({
    queryKey: ['outputs', id],
    queryFn: () => outputApi.getOutput(id!),
    enabled: !!id,
  });
}
