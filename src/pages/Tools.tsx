import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Wrench, Search, Users } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useOfficeAgents } from '@/hooks/useAgents';
import type { OfficeAgent } from '@/types';

/**
 * 工具中心页面
 * 展示办公室所有 Agent 拥有的工具能力，以及每个工具被多少 Agent 使用
 */
export default function Tools() {
  const { data: agents = [], isLoading } = useOfficeAgents();
  const [search, setSearch] = useState('');

  // 根据 Agent 数据计算每个工具的使用情况
  const toolStats = useMemo(() => computeToolStats(agents), [agents]);

  // 按搜索关键字过滤
  const filteredTools = useMemo(() => {
    return toolStats.filter((t) => t.name.toLowerCase().includes(search.toLowerCase()));
  }, [toolStats, search]);

  return (
    <PageWrapper className="space-y-6">
      {/* 页面标题 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold font-display">工具中心</h1>
          <p className="text-sm text-muted-foreground">管理并查看所有 Agent 可调用的工具能力</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索工具名称..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-40 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            共 {filteredTools.length} 个工具，{agents.length} 名 Agent 可使用
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredTools.map((tool) => (
              <ToolCard key={tool.name} tool={tool} />
            ))}
          </div>
        </>
      )}
    </PageWrapper>
  );
}

/**
 * 单个工具卡片：展示工具名、使用人数和使用者头像列表
 */
function ToolCard({ tool }: { tool: ToolStat }) {
  return (
    <Card className="p-5 transition-all hover:border-primary/50 hover:shadow-soft">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Wrench className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold">{tool.name}</h3>
          <p className="text-xs text-muted-foreground">{tool.agents.length} 名 Agent 可用</p>
        </div>
      </div>

      {/* 使用者列表 */}
      <div className="flex items-center justify-between">
        <div className="flex -space-x-2">
          {tool.agents.slice(0, 5).map((agent) => (
            <img
              key={agent.id}
              src={agent.avatar}
              alt={agent.name}
              className="h-8 w-8 rounded-full border-2 border-card"
              title={agent.name}
            />
          ))}
          {tool.agents.length > 5 && (
            <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-card bg-muted text-xs font-medium">
              +{tool.agents.length - 5}
            </div>
          )}
        </div>

        {tool.agents.length > 0 && (
          <Link
            to={`/profile/${tool.agents[0].id}`}
            className="text-xs text-primary hover:underline"
          >
            查看详情
          </Link>
        )}
      </div>

      {/* 简单标签：根据使用人数判断重要性 */}
      <div className="mt-4 flex flex-wrap gap-2">
        {tool.agents.length >= 3 && <Badge variant="secondary" className="text-xs">核心工具</Badge>}
        {tool.agents.length === 1 && <Badge variant="outline" className="text-xs">专用工具</Badge>}
      </div>
    </Card>
  );
}

/**
 * 工具统计数据结构
 */
interface ToolStat {
  name: string;
  agents: OfficeAgent[];
}

/**
 * 计算每个工具被哪些 Agent 使用
 */
function computeToolStats(agents: OfficeAgent[]): ToolStat[] {
  const map = new Map<string, OfficeAgent[]>();

  agents.forEach((agent) => {
    agent.tools.forEach((tool) => {
      if (!map.has(tool)) {
        map.set(tool, []);
      }
      map.get(tool)!.push(agent);
    });
  });

  return Array.from(map.entries())
    .map(([name, list]) => ({ name, agents: list }))
    .sort((a, b) => b.agents.length - a.agents.length);
}
