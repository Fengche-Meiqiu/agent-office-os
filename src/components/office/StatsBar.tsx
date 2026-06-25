import { Users, Activity, Clock, CheckCircle2, Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface StatsBarProps {
  total: number;
  online: number;
  working: number;
  completedToday: number;
  running: number;
}

const stats = [
  { key: 'total', label: 'Agent 总数', icon: Users },
  { key: 'online', label: '在线', icon: Activity },
  { key: 'working', label: '忙碌中', icon: Clock },
  { key: 'completed', label: '今日完成任务', icon: CheckCircle2 },
  { key: 'running', label: '进行中任务', icon: Loader2 },
] as const;

export function StatsBar({ total, online, working, completedToday, running }: StatsBarProps) {
  const values: Record<string, number> = {
    total,
    online,
    working,
    completed: completedToday,
    running,
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.key} className="p-4 flex items-center gap-3 hover:shadow-soft transition-shadow">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-xl font-bold">{values[stat.key]}</p>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
