import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useTasks } from '@/hooks/useTasks';
import type { TaskStatus } from '@/types';

const statusFilters: TaskStatus[] = ['Pending', 'Running', 'Completed', 'Failed', 'Cancelled'];

const statusLabels: Record<TaskStatus, string> = {
  Pending: '待处理',
  Running: '运行中',
  Completed: '已完成',
  Failed: '失败',
  Cancelled: '已取消',
};

const statusColors: Record<TaskStatus, string> = {
  Pending: 'bg-yellow-100 text-yellow-700',
  Running: 'bg-blue-100 text-blue-700',
  Completed: 'bg-green-100 text-green-700',
  Failed: 'bg-red-100 text-red-700',
  Cancelled: 'bg-gray-100 text-gray-700',
};

export default function Tasks() {
  const { data: tasks = [], isLoading } = useTasks();
  const [filter, setFilter] = useState<TaskStatus | '全部'>('全部');

  const filteredTasks = filter === '全部' ? tasks : tasks.filter((t) => t.status === filter);

  return (
    <PageWrapper className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-display">任务中心</h1>
        <p className="text-sm text-muted-foreground">查看和管理所有 Agent 执行的任务</p>
      </div>

      {/* 筛选 */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge
          variant={filter === '全部' ? 'default' : 'outline'}
          className="cursor-pointer"
          onClick={() => setFilter('全部')}
        >
          全部
        </Badge>
        {statusFilters.map((s) => (
          <Badge
            key={s}
            variant={filter === s ? 'default' : 'outline'}
            className="cursor-pointer"
            onClick={() => setFilter(s)}
          >
            {statusLabels[s]}
          </Badge>
        ))}
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50 text-left text-muted-foreground">
                <th className="px-5 py-3 font-medium">任务名称</th>
                <th className="px-5 py-3 font-medium">执行员工</th>
                <th className="px-5 py-3 font-medium">状态</th>
                <th className="px-5 py-3 font-medium">开始时间</th>
                <th className="px-5 py-3 font-medium">结束时间</th>
                <th className="px-5 py-3 font-medium">耗时</th>
                <th className="px-5 py-3 font-medium">成果</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center">
                    <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  </td>
                </tr>
              ) : (
                filteredTasks.map((task) => (
                  <tr key={task.id} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="px-5 py-3 font-medium">{task.name}</td>
                    <td className="px-5 py-3">{task.agentName}</td>
                    <td className="px-5 py-3">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[task.status]}`}>
                        {statusLabels[task.status]}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {task.startedAt ? new Date(task.startedAt).toLocaleString('zh-CN') : '-'}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {task.endedAt ? new Date(task.endedAt).toLocaleString('zh-CN') : '-'}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {task.duration ? `${task.duration} 分钟` : '-'}
                    </td>
                    <td className="px-5 py-3">
                      {task.outputId ? (
                        <Link to="/outputs" className="text-primary hover:underline">查看成果</Link>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </PageWrapper>
  );
}
