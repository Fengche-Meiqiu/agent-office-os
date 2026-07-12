import { useState, useMemo, useEffect } from 'react';
import { Search, RefreshCw } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { MarketplaceAgentCard } from '@/components/marketplace/MarketplaceAgentCard';
import { useMarketplaceAgents, useOfficeAgents, useHireAgent, useSyncMarketplace } from '@/hooks/useAgents';
const statusFilters = ['全部', 'ONLINE', 'BUSY', 'OFFLINE'];

export default function Marketplace() {
  const { data: marketplaceAgents = [], isLoading: marketLoading } = useMarketplaceAgents();
  const { data: officeAgents = [], isLoading: officeLoading } = useOfficeAgents();
  const hireMutation = useHireAgent();
  const syncMutation = useSyncMarketplace();

  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('全部');
  // 小白解释：防止同步反复触发，只自动同步一次
  const [hasAutoSynced, setHasAutoSynced] = useState(false);

  // 小白解释：进入人才市场时，如果列表为空且没在加载，自动从 Hermes 同步一次。
  // 这样用户不用手动点"刷新人才库"也能看到 Agent。
  // 注意：依赖数组里不写 syncMutation，因为 mutate 函数每次渲染都是新引用，
  // 放进去会导致 effect 反复触发，引发 React 死循环。
  useEffect(() => {
    if (!marketLoading && marketplaceAgents.length === 0 && !syncMutation.isPending && !hasAutoSynced) {
      setHasAutoSynced(true);
      syncMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marketLoading, marketplaceAgents.length, syncMutation.isPending, hasAutoSynced]);

  const hiredIds = useMemo(() => new Set(officeAgents.map((a) => a.marketplaceId)), [officeAgents]);

  const filteredAgents = useMemo(() => {
    return marketplaceAgents.filter((agent) => {
      const matchSearch =
        agent.name.toLowerCase().includes(search.toLowerCase()) ||
        agent.title.toLowerCase().includes(search.toLowerCase()) ||
        agent.skills.some((s) => s.toLowerCase().includes(search.toLowerCase()));
      const matchStatus = selectedStatus === '全部' || agent.status === selectedStatus;
      return agent.platform === 'Hermes' && matchSearch && matchStatus;
    });
  }, [marketplaceAgents, search, selectedStatus]);

  const handleHire = (agentId: string) => {
    hireMutation.mutate(agentId);
  };

  return (
    <PageWrapper className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-display">人才市场</h1>
          <p className="text-sm text-muted-foreground">浏览来自 Hermes 平台的真实 Agent 人才库</p>
        </div>
        {/* 小白解释：V2 不再自动同步，需要手动点"刷新人才库"从 Hermes 拉取 Agent */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending || marketLoading}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
          {syncMutation.isPending ? '同步中...' : '刷新人才库'}
        </Button>
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
