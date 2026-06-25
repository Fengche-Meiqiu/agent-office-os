import { useMemo } from 'react';
import { CheckCircle2, Users, FolderOpen, MessageSquare } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { useOfficeAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { useMeetings } from '@/hooks/useMeetings';
import { useOutputs } from '@/hooks/useOutputs';
import type { TaskStatus } from '@/types';

// 任务状态颜色映射
const statusColors: Record<TaskStatus, string> = {
  Pending: '#EAB308',
  Running: '#3B82F6',
  Completed: '#22C55E',
  Failed: '#EF4444',
  Cancelled: '#94A3B8',
};

const statusLabels: Record<TaskStatus, string> = {
  Pending: '待处理',
  Running: '运行中',
  Completed: '已完成',
  Failed: '失败',
  Cancelled: '已取消',
};

/**
 * 数据看板页面
 * 汇总展示 Agent 团队、任务、会议、成果等核心指标
 */
export default function Dashboard() {
  const { data: agents = [], isLoading: agentsLoading } = useOfficeAgents();
  const { data: tasks = [], isLoading: tasksLoading } = useTasks();
  const { data: meetings = [], isLoading: meetingsLoading } = useMeetings();
  const { data: outputs = [], isLoading: outputsLoading } = useOutputs();

  // 关键指标
  const totalAgents = agents.length;
  const onlineAgents = agents.filter((a) => a.status === 'ONLINE').length;
  const completedTasks = tasks.filter((t) => t.status === 'Completed').length;
  const totalOutputs = outputs.length;

  // 任务状态分布数据（给饼图用）
  const taskStatusData = useMemo(() => {
    const counts: Record<TaskStatus, number> = {
      Pending: 0,
      Running: 0,
      Completed: 0,
      Failed: 0,
      Cancelled: 0,
    };
    tasks.forEach((t) => {
      counts[t.status] = (counts[t.status] || 0) + 1;
    });
    return (Object.keys(counts) as TaskStatus[]).map((status) => ({
      name: statusLabels[status],
      value: counts[status],
      color: statusColors[status],
    }));
  }, [tasks]);

  // Agent 任务数量排行（给柱状图用）
  const agentTaskData = useMemo(() => {
    return agents
      .map((agent) => ({
        name: agent.name,
        tasks: tasks.filter((t) => t.agentId === agent.id).length,
      }))
      .sort((a, b) => b.tasks - a.tasks)
      .slice(0, 6);
  }, [agents, tasks]);

  const isLoading = agentsLoading || tasksLoading || meetingsLoading || outputsLoading;

  return (
    <PageWrapper className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold font-display">数据看板</h1>
        <p className="text-sm text-muted-foreground">实时查看 Agent 办公室的运行指标</p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      ) : (
        <>
          {/* 指标卡片 */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              icon={Users}
              label="Agent 总数"
              value={totalAgents}
              subLabel={`${onlineAgents} 人在线`}
              color="text-blue-600"
            />
            <MetricCard
              icon={CheckCircle2}
              label="已完成任务"
              value={completedTasks}
              subLabel={`共 ${tasks.length} 个任务`}
              color="text-green-600"
            />
            <MetricCard
              icon={MessageSquare}
              label="会议总数"
              value={meetings.length}
              subLabel="包含已完成与进行中"
              color="text-purple-600"
            />
            <MetricCard
              icon={FolderOpen}
              label="成果文件"
              value={totalOutputs}
              subLabel="任务 / 会议 / 上传"
              color="text-orange-600"
            />
          </div>

          {/* 图表区 */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* 任务状态分布 */}
            <Card className="p-5">
              <h3 className="mb-4 font-semibold">任务状态分布</h3>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={taskStatusData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(entry) => `${entry.name}: ${entry.value}`}
                    >
                      {taskStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Agent 任务数排行 */}
            <Card className="p-5">
              <h3 className="mb-4 font-semibold">Agent 任务数排行</h3>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={agentTaskData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="tasks" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </>
      )}
    </PageWrapper>
  );
}

/**
 * 指标卡片组件：展示一个大数字和一行说明
 */
function MetricCard({
  icon: Icon,
  label,
  value,
  subLabel,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  subLabel: string;
  color: string;
}) {
  return (
    <Card className="flex items-center gap-4 p-5 transition-all hover:shadow-soft">
      <div className={`rounded-xl bg-secondary/70 p-3 ${color}`}>
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-muted-foreground">{subLabel}</p>
      </div>
    </Card>
  );
}
