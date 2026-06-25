import { useEventLogs } from '@/hooks/useEventLogs';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Calendar, CheckSquare, Bot, AlertCircle } from 'lucide-react';
import type { EventLog } from '@/types';

const typeIcons: Record<EventLog['type'], React.ElementType> = {
  task: CheckSquare,
  meeting: Calendar,
  system: AlertCircle,
  agent: Bot,
};

const typeColors: Record<EventLog['type'], string> = {
  task: 'bg-blue-100 text-blue-600',
  meeting: 'bg-purple-100 text-purple-600',
  system: 'bg-gray-100 text-gray-600',
  agent: 'bg-emerald-100 text-emerald-600',
};

export function ActivityFeed() {
  const { data: logs = [], isLoading } = useEventLogs();

  return (
    <Card className="h-full flex flex-col">
      <div className="flex items-center justify-between border-b p-4">
        <h3 className="font-semibold">任务动态</h3>
        <span className="text-xs text-primary cursor-pointer hover:underline">全部任务</span>
      </div>
      <ScrollArea className="flex-1 p-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {logs.slice(0, 8).map((log) => {
              const Icon = typeIcons[log.type];
              return (
                <div key={log.id} className="flex items-start gap-3">
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${typeColors[log.type]}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{log.title}</p>
                    <p className="text-xs text-muted-foreground">{log.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ScrollArea>

      <div className="border-t p-4">
        <h4 className="mb-3 text-sm font-semibold">最近活动</h4>
        <div className="space-y-2">
          {logs.slice(0, 5).map((log) => (
            <div key={`recent-${log.id}`} className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground truncate">{log.title}</span>
              <span className="text-muted-foreground shrink-0">{log.description}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
