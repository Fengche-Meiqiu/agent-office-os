import { Link } from 'react-router-dom';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Card } from '@/components/ui/card';
import type { OfficeAgent } from '@/types';

interface AgentCardProps {
  agent: OfficeAgent;
  todayTask?: string;
}

export function AgentCard({ agent, todayTask }: AgentCardProps) {
  return (
    <Link to={`/profile/${agent.id}`}>
      <Card className="group relative overflow-hidden p-4 transition-all hover:-translate-y-1 hover:shadow-card cursor-pointer">
        <div className="flex flex-col items-center text-center">
          <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="lg" />
          <h3 className="mt-3 font-semibold">{agent.name}</h3>
          <p className="text-xs text-muted-foreground">{agent.title}</p>
          <div className="mt-2">
            <StatusBadge status={agent.status} size="sm" />
          </div>
          {todayTask && (
            <div className="mt-3 w-full rounded-md bg-secondary/60 px-2 py-1.5 text-xs text-muted-foreground line-clamp-2">
              {todayTask}
            </div>
          )}
        </div>
      </Card>
    </Link>
  );
}
