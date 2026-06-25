import { Bell, CheckCheck, Clock, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useEventLogs, useClearEventLogs } from '@/hooks/useEventLogs';

/**
 * 通知面板
 * 展示最近的系统事件日志，支持一键清空
 */
interface NotificationPanelProps {
  onClose?: () => void;
}

export function NotificationPanel({ onClose }: NotificationPanelProps) {
  const { data: logs = [], isLoading } = useEventLogs();
  const clearMutation = useClearEventLogs();

  const handleClear = () => {
    clearMutation.mutate(undefined, {
      onSuccess: () => onClose?.(),
    });
  };

  return (
    <Card className="w-80 overflow-hidden p-0 shadow-card animate-in fade-in zoom-in-95 duration-200">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2 font-semibold">
          <Bell className="h-4 w-4 text-primary" />
          通知
        </div>
        {logs.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-auto px-2 py-1 text-xs"
            onClick={handleClear}
            disabled={clearMutation.isPending}
          >
            <CheckCheck className="mr-1 h-3 w-3" />
            清空
          </Button>
        )}
      </div>

      <ScrollArea className="max-h-[360px]">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 px-4 py-8 text-sm text-muted-foreground">
            <Bell className="h-8 w-8 opacity-30" />
            <p>暂无新通知</p>
          </div>
        ) : (
          <div className="divide-y">
            {logs.slice(0, 20).map((log) => (
              <div key={log.id} className="flex gap-3 px-4 py-3 hover:bg-accent/50">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <AlertCircle className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium leading-snug">{log.title}</p>
                  <p className="text-xs text-muted-foreground">{log.description}</p>
                  <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {new Date(log.timestamp).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </Card>
  );
}
