import { useQuery } from '@tanstack/react-query';
import { outputApi } from '@/lib/api';

// 鑾峰彇鎴愭灉鍒楄〃
export function useOutputs() {
  return useQuery({
    queryKey: ['outputs'],
    queryFn: () => outputApi.getOutputs(),
  });
}

// 鑾峰彇鍗曚釜鎴愭灉
export function useOutput(id: string | undefined) {
  return useQuery({
    queryKey: ['outputs', id],
    queryFn: () => outputApi.getOutput(id!),
    enabled: !!id,
  });
}
