import { useState, useMemo } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { MarketplaceAgentCard } from '@/components/marketplace/MarketplaceAgentCard';
import { useMarketplaceAgents, useOfficeAgents, useHireAgent } from '@/hooks/useAgents';
import type { Platform } from '@/types';

const platforms: Platform[] = ['Hermes', 'OpenClaw', 'CrewAI', 'LangGraph'];
const statusFilters = ['全部', 'ONLINE', 'BUSY', 'OFFLINE'];

export default function Marketplace() {
  const { data: marketplaceAgents = [], isLoading: marketLoading } = useMarketplaceAgents();
  const { data: officeAgents = [], isLoading: officeLoading } = useOfficeAgents();
  const hireMutation = useHireAgent();

  const [search, setSearch] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | '全部'>('全部');
  const [selectedStatus, setSelectedStatus] = useState<string>('全部');

  const hiredIds = useMemo(() => new Set(officeAgents.map((a) => a.marketplaceId)), [officeAgents]);

  const filteredAgents = useMemo(() => {
    return marketplaceAgents.filter((agent) => {
      const matchSearch =
        agent.name.toLowerCase().includes(search.toLowerCase()) ||
        agent.title.toLowerCase().includes(search.toLowerCase()) ||
        agent.skills.some((s) => s.toLowerCase().includes(search.toLowerCase()));
      const matchPlatform = selectedPlatform === '全部' || agent.platform === selectedPlatform;
      const matchStatus = selectedStatus === '全部' || agent.status === selectedStatus;
      return matchSearch && matchPlatform && matchStatus;
    });
  }, [marketplaceAgents, search, selectedPlatform, selectedStatus]);

  const handleHire = (agentId: string) => {
    hireMutation.mutate(agentId);
  };

  return (
    <PageWrapper className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-display">人才市场</h1>
        <p className="text-sm text-muted-foreground">浏览来自 Hermes、OpenClaw 等平台的 Agent 人才库</p>
      </div>

      {/* 搜索与筛选 */}
      <div className="space-y-4 rounded-xl bg-card p-4 border shadow-sm">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索 Agent 名称、职位、技能..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">平台：</span>
          {(['全部', ...platforms] as const).map((p) => (
            <Badge
              key={p}
              variant={selectedPlatform === p ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedPlatform(p)}
            >
              {p}
            </Badge>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">状态：</span>
          {statusFilters.map((s) => (
            <Badge
              key={s}
              variant={selectedStatus === s ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedStatus(s)}
            >
              {s}
            </Badge>
          ))}
        </div>
      </div>

      {/* Agent 列表 */}
      {marketLoading || officeLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            共找到 {filteredAgents.length} 个 Agent
          </p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredAgents.map((agent) => (
              <MarketplaceAgentCard
                key={agent.id}
                agent={agent}
                isHired={hiredIds.has(agent.id)}
                onHire={handleHire}
                hiring={hireMutation.isPending}
              />
            ))}
          </div>
        </>
      )}
    </PageWrapper>
  );
}
