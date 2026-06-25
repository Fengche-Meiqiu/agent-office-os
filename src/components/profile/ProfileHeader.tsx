import { Link, useNavigate } from 'react-router-dom';
import { MessageSquare, UserX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { PlatformBadge } from '@/components/shared/PlatformBadge';
import { useFireAgent } from '@/hooks/useAgents';
import type { OfficeAgent } from '@/types';

interface ProfileHeaderProps {
  agent: OfficeAgent;
}

export function ProfileHeader({ agent }: ProfileHeaderProps) {
  const navigate = useNavigate();
  const fireMutation = useFireAgent();

  const handleFire = () => {
    if (confirm(`确定要解雇 ${agent.name} 吗？`)) {
      fireMutation.mutate(agent.id, {
        onSuccess: () => navigate('/'),
      });
    }
  };

  return (
    <div className="flex flex-col gap-4 rounded-xl bg-card p-5 border shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-4">
        <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="xl" />
        <div>
          <h1 className="text-2xl font-bold font-display">
            {agent.name}
            <span className="ml-2 text-base font-normal text-muted-foreground">({agent.title})</span>
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <PlatformBadge platform={agent.platform} />
            <StatusBadge status={agent.status} size="sm" />
            <span className="text-xs text-muted-foreground">
              雇佣时间：{new Date(agent.hiredAt).toLocaleDateString('zh-CN')}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Link to={`/chat/${agent.id}`}>
          <Button variant="outline" className="gap-2">
            <MessageSquare className="h-4 w-4" />
            聊天
          </Button>
        </Link>
        <Button variant="destructive" className="gap-2" onClick={handleFire} disabled={fireMutation.isPending}>
          <UserX className="h-4 w-4" />
          解雇
        </Button>
      </div>
    </div>
  );
}
