import { useMemo, useState } from 'react';
import { RefreshCw, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { MarketplaceAgentCard } from '@/components/marketplace/MarketplaceAgentCard';
import { useHireAgent, useMarketplaceAgents, useOfficeAgents, useSyncMarketplaceAgents } from '@/hooks/useAgents';
import type { Platform } from '@/types';

const platforms: Platform[] = ['Hermes', 'OpenClaw', 'CrewAI', 'LangGraph'];
const statusFilters = ['All', 'ONLINE', 'BUSY', 'OFFLINE'];

export default function Marketplace() {
  const { data: marketplaceAgents = [], isLoading: marketLoading } = useMarketplaceAgents();
  const { data: officeAgents = [], isLoading: officeLoading } = useOfficeAgents();
  const hireMutation = useHireAgent();
  const syncMutation = useSyncMarketplaceAgents();

  const [search, setSearch] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | 'All'>('All');
  const [selectedStatus, setSelectedStatus] = useState<string>('All');

  const hiredIds = useMemo(() => new Set(officeAgents.map((agent) => agent.marketplaceId)), [officeAgents]);

  const filteredAgents = useMemo(() => {
    const keyword = search.toLowerCase();
    return marketplaceAgents.filter((agent) => {
      const matchSearch =
        agent.name.toLowerCase().includes(keyword) ||
        agent.title.toLowerCase().includes(keyword) ||
        agent.description.toLowerCase().includes(keyword) ||
        agent.skills.some((skill) => skill.toLowerCase().includes(keyword));
      const matchPlatform = selectedPlatform === 'All' || agent.platform === selectedPlatform;
      const matchStatus = selectedStatus === 'All' || agent.status === selectedStatus;
      return matchSearch && matchPlatform && matchStatus;
    });
  }, [marketplaceAgents, search, selectedPlatform, selectedStatus]);

  const loading = marketLoading || officeLoading;

  return (
    <PageWrapper className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold font-display">Agent Talent Library</h1>
          <p className="text-sm text-muted-foreground">Browse agents synced from Hermes and hire them into your office.</p>
        </div>
        <Button variant="outline" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending} className="gap-2">
          <RefreshCw className={`h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
          Refresh talent library
        </Button>
      </div>

      <div className="space-y-4 rounded-lg bg-card p-4 border shadow-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search name, role, description, or skill"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Platform</span>
          {(['All', ...platforms] as const).map((platform) => (
            <Badge
              key={platform}
              variant={selectedPlatform === platform ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedPlatform(platform)}
            >
              {platform}
            </Badge>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Status</span>
          {statusFilters.map((status) => (
            <Badge
              key={status}
              variant={selectedStatus === status ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedStatus(status)}
            >
              {status}
            </Badge>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div key={item} className="h-64 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">{filteredAgents.length} agents found</p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredAgents.map((agent) => (
              <MarketplaceAgentCard
                key={agent.id}
                agent={agent}
                isHired={hiredIds.has(agent.id)}
                onHire={(agentId) => hireMutation.mutate(agentId)}
                hiring={hireMutation.isPending}
              />
            ))}
          </div>
        </>
      )}
    </PageWrapper>
  );
}
