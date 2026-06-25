import { useState } from 'react';
import { Wrench, UserPlus, Eye } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { PlatformBadge } from '@/components/shared/PlatformBadge';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import type { MarketplaceAgent } from '@/types';

interface MarketplaceAgentCardProps {
  agent: MarketplaceAgent;
  isHired: boolean;
  onHire: (agentId: string) => void;
  hiring: boolean;
}

export function MarketplaceAgentCard({ agent, isHired, onHire, hiring }: MarketplaceAgentCardProps) {
  const [detailOpen, setDetailOpen] = useState(false);

  return (
    <Card className="group overflow-hidden transition-all hover:-translate-y-1 hover:shadow-card">
      <div className="flex gap-4 p-4">
        <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="lg" />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold">{agent.name}</h3>
              <p className="text-xs text-muted-foreground">{agent.title}</p>
            </div>
            <PlatformBadge platform={agent.platform} />
          </div>

          <div className="mt-2 flex items-center gap-2">
            <StatusBadge status={agent.status} size="sm" />
          </div>

          <div className="mt-3 space-y-2">
            <div className="flex flex-wrap gap-1">
              {agent.skills.slice(0, 4).map((skill) => (
                <Badge key={skill} variant="secondary" className="text-xs font-normal">
                  {skill}
                </Badge>
              ))}
              {agent.skills.length > 4 && (
                <Badge variant="secondary" className="text-xs font-normal">+{agent.skills.length - 4}</Badge>
              )}
            </div>
            <div className="flex flex-wrap gap-1">
              {agent.tools.slice(0, 3).map((tool) => (
                <span key={tool} className="text-xs text-muted-foreground flex items-center gap-0.5">
                  <Wrench className="h-3 w-3" />
                  {tool}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2">
            <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="gap-1 flex-1">
                  <Eye className="h-3.5 w-3.5" />
                  查看详情
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <div className="flex items-center gap-3">
                    <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="lg" />
                    <div>
                      <DialogTitle>{agent.name}</DialogTitle>
                      <DialogDescription>{agent.title}</DialogDescription>
                    </div>
                  </div>
                </DialogHeader>
                <div className="space-y-4 py-2">
                  <p className="text-sm text-muted-foreground">{agent.description}</p>
                  <div>
                    <p className="mb-1 text-sm font-medium">技能</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.skills.map((skill) => (
                        <Badge key={skill} variant="secondary">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="mb-1 text-sm font-medium">工具能力</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.tools.map((tool) => (
                        <Badge key={tool} variant="outline">{tool}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">平台：</span>
                    <PlatformBadge platform={agent.platform} />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setDetailOpen(false)}>取消</Button>
                  <Button
                    onClick={() => { onHire(agent.id); setDetailOpen(false); }}
                    disabled={isHired || hiring}
                    className="gap-1"
                  >
                    <UserPlus className="h-4 w-4" />
                    {isHired ? '已雇佣' : '雇佣'}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Button
              size="sm"
              className="gap-1 flex-1"
              disabled={isHired || hiring}
              onClick={() => onHire(agent.id)}
            >
              <UserPlus className="h-3.5 w-3.5" />
              {isHired ? '已雇佣' : '雇佣'}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
