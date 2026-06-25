import { Link } from 'react-router-dom';
import { Network, Users } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useOfficeAgents } from '@/hooks/useAgents';
import type { OfficeAgent } from '@/types';

/**
 * 组织架构页面
 * 把已雇佣的 Agent 按部门分组，以树状图形式展示公司层级关系
 */
export default function Organization() {
  const { data: agents = [], isLoading } = useOfficeAgents();

  // 按部门名称把 Agent 分组
  const departments = groupByDepartment(agents);

  return (
    <PageWrapper className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold font-display">组织架构</h1>
        <p className="text-sm text-muted-foreground">查看 AI Agent 团队的公司层级与部门分布</p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          {/* 顶层 CEO 节点 */}
          <div className="flex justify-center">
            <Card className="flex w-64 items-center gap-4 p-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white">
                <Network className="h-6 w-6" />
              </div>
              <div>
                <p className="font-semibold">CEO</p>
                <p className="text-xs text-muted-foreground">公司负责人</p>
              </div>
            </Card>
          </div>

          {/* 连接线（纯装饰） */}
          <div className="relative flex justify-center">
            <div className="absolute top-0 h-6 w-px bg-border" />
            <div className="absolute top-6 h-px w-[80%] max-w-3xl bg-border" />
          </div>

          {/* 部门卡片网格 */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {departments.map((dept) => (
              <DepartmentCard key={dept.name} department={dept} />
            ))}
          </div>
        </div>
      )}
    </PageWrapper>
  );
}

/**
 * 单个部门卡片：显示部门名称与下面的 Agent 列表
 */
function DepartmentCard({ department }: { department: DepartmentGroup }) {
  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Users className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold">{department.name}</h3>
          <p className="text-xs text-muted-foreground">{department.agents.length} 名员工</p>
        </div>
      </div>

      <div className="space-y-2">
        {department.agents.map((agent) => (
          <Link
            key={agent.id}
            to={`/profile/${agent.id}`}
            className="flex items-center gap-3 rounded-lg border p-3 transition-all hover:border-primary/50 hover:bg-accent/50"
          >
            <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="sm" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{agent.name}</p>
              <p className="truncate text-xs text-muted-foreground">{agent.title}</p>
            </div>
            <StatusBadge status={agent.status} size="sm" />
          </Link>
        ))}
      </div>
    </Card>
  );
}

/**
 * 部门分组数据结构
 */
interface DepartmentGroup {
  name: string;
  agents: OfficeAgent[];
}

/**
 * 把 Agent 列表按 department 字段分组
 * 没有部门的统一放到“未分配”里
 */
function groupByDepartment(agents: OfficeAgent[]): DepartmentGroup[] {
  const map = new Map<string, OfficeAgent[]>();

  agents.forEach((agent) => {
    const dept = agent.department || '未分配';
    if (!map.has(dept)) {
      map.set(dept, []);
    }
    map.get(dept)!.push(agent);
  });

  return Array.from(map.entries()).map(([name, list]) => ({
    name,
    agents: list,
  }));
}
