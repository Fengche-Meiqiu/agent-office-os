/**
 * SSE 实时推送 Hook（V2 新增）
 *
 * 小白解释：这个 hook 帮你连上后端的"实时通道"，
 * 后端有任务进度更新、会议消息、Agent 状态变化时，会自动推过来，
 * 不需要你手动刷新页面。
 *
 * 用法：
 *   const { isConnected } = useSSE('tasks', {
 *     task_status: (data) => console.log('任务状态变了', data),
 *     task_progress: (data) => console.log('进度更新', data),
 *   });
 */
import { useEffect, useRef, useState } from 'react';
import { createSSEConnection } from '@/lib/api';

export function useSSE(
  channel: 'tasks' | 'meetings',
  handlers: Record<string, (data: any) => void>
) {
  const [isConnected, setIsConnected] = useState(false);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  useEffect(() => {
    // 仅在非 Mock 模式下连接 SSE（Mock 模式没有后端）
    const cleanup = createSSEConnection(channel, {
      connected: () => setIsConnected(true),
      ...handlersRef.current,
    });

    return () => {
      cleanup();
      setIsConnected(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [channel]);

  return { isConnected };
}
