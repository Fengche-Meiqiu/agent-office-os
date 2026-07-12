import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle2, XCircle, Calendar, Search } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { ProfileHeader } from '@/components/profile/ProfileHeader';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useOfficeAgent } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { useChatMessages } from '@/hooks/useChats';
import { AgentAvatar } from '@/components/shared/AgentAvatar';

const tabItems = [
  { value: 'basic', label: '基本信息' },
  { value: 'soul', label: 'Soul' },
  { value: 'skills', label: 'Skills' },
  { value: 'tools', label: 'Tools' },
  { value: 'memory', label: 'Memory' },
  { value: 'tasks', label: 'Task History' },
  { value: 'chats', label: 'Chat History' },
  { value: 'performance', label: 'Performance' },
  { value: 'employment', label: 'Employment' },
];

export default function Profile() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState('basic');
  const [memorySearch, setMemorySearch] = useState('');

  const { data: agent, isLoading } = useOfficeAgent(id);
  const { data: allTasks = [] } = useTasks();
  const { data: messages = [] } = useChatMessages(id);

  if (isLoading) {
    return (
      <PageWrapper className="space-y-6">
        <div className="h-32 animate-pulse rounded-xl bg-muted" />
        <div className="h-96 animate-pulse rounded-xl bg-muted" />
      </PageWrapper>
    );
  }

  if (!agent) {
    return (
      <PageWrapper className="flex h-full flex-col items-center justify-center text-center">
        <h2 className="text-xl font-semibold">未找到该员工</h2>
        <p className="text-muted-foreground">Agent ID: {id}</p>
        <Link to="/" className="mt-4 text-primary hover:underline">返回办公室</Link>
      </PageWrapper>
    );
  }

  const agentTasks = allTasks.filter((t) => t.agentId === agent.id).slice(0, 100);
  const filteredMemory = agent.memory.filter((m) =>
    m.toLowerCase().includes(memorySearch.toLowerCase())
  );

  return (
    <PageWrapper className="space-y-6">
      <ProfileHeader agent={agent} />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <ScrollArea className="w-full">
          <TabsList className="w-auto inline-flex min-w-full">
            {tabItems.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </ScrollArea>

        {/* 基本信息 */}
        <TabsContent value="basic">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">基本信息</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <InfoItem label="Agent ID" value={agent.id} />
              <InfoItem label="平台 ID" value={agent.platformAgentId} />
              <InfoItem label="平台" value={agent.platform} />
              <InfoItem label="职位" value={agent.title || '待上线'} />
              <InfoItem label="创建时间" value={new Date(agent.hiredAt).toLocaleString('zh-CN')} />
              <InfoItem label="最后活跃时间" value={new Date(agent.lastActiveAt).toLocaleString('zh-CN')} />
              <InfoItem label="部门" value={agent.department || '待上线'} />
              <InfoItem label="直属上级" value={agent.managerId === 'ceo' ? 'CEO' : agent.managerId || '待上线'} />
            </div>
          </Card>
        </TabsContent>

        {/* Soul */}
        <TabsContent value="soul">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Soul（人格）</h3>
            <div className="space-y-4">
              <SoulItem label="身份" value={agent.soul?.identity || '待上线'} />
              <SoulItem label="目标" value={agent.soul?.goal || '待上线'} />
              <SoulItem label="原则" value={agent.soul?.principles || '待上线'} />
              <SoulItem label="行为风格" value={agent.soul?.style || '待上线'} />
              <SoulItem label="人格描述" value={agent.soul?.description || '待上线'} />
            </div>
          </Card>
        </TabsContent>

        {/* Skills */}
        <TabsContent value="skills">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Skills（技能）</h3>
            <div className="flex flex-wrap gap-2">
              {agent.skills.map((skill) => (
                <Badge key={skill} className="px-3 py-1 text-sm bg-primary/10 text-primary hover:bg-primary/10">
                  {skill}
                </Badge>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Tools */}
        <TabsContent value="tools">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Tools（工具能力）</h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
              {agent.tools.map((tool) => (
                <div
                  key={tool}
                  className="flex items-center gap-2 rounded-lg border bg-card p-3 text-sm font-medium transition-all hover:border-primary/50 hover:shadow-sm"
                >
                  <div className="h-2 w-2 rounded-full bg-primary" />
                  {tool}
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Memory */}
        <TabsContent value="memory">
          <Card className="p-6">
            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <h3 className="text-lg font-semibold">Memory（记忆）</h3>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="搜索记忆..."
                  value={memorySearch}
                  onChange={(e) => setMemorySearch(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <div className="space-y-2">
              {filteredMemory.map((memory, index) => (
                <div key={index} className="rounded-lg bg-secondary/50 p-3 text-sm">
                  {memory}
                </div>
              ))}
              {filteredMemory.length === 0 && (
                <p className="text-sm text-muted-foreground">未找到匹配的记忆</p>
              )}
            </div>
            <p className="mt-4 text-xs text-muted-foreground">V1 仅支持只读查看，禁止修改</p>
          </Card>
        </TabsContent>

        {/* Task History */}
        <TabsContent value="tasks">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Task History</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 font-medium">任务名称</th>
                    <th className="pb-2 font-medium">时间</th>
                    <th className="pb-2 font-medium">状态</th>
                    <th className="pb-2 font-medium">成果</th>
                  </tr>
                </thead>
                <tbody>
                  {agentTasks.map((task) => (
                    <tr key={task.id} className="border-b last:border-0">
                      <td className="py-3">{task.name}</td>
                      <td className="py-3 text-muted-foreground">
                        {task.endedAt
                          ? new Date(task.endedAt).toLocaleString('zh-CN')
                          : task.startedAt
                          ? new Date(task.startedAt).toLocaleString('zh-CN')
                          : '-'}
                      </td>
                      <td className="py-3">
                        <TaskStatusBadge status={task.status} />
                      </td>
                      <td className="py-3">
                        {task.outputId ? (
                          <Link to="/outputs" className="text-primary hover:underline">查看成果</Link>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>

        {/* Chat History */}
        <TabsContent value="chats">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Chat History</h3>
            <div className="space-y-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  {msg.role === 'agent' ? (
                    <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="sm" />
                  ) : (
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs text-white">我</div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                      msg.role === 'user'
                        ? 'bg-primary text-white'
                        : 'bg-secondary'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {messages.length === 0 && (
                <p className="text-sm text-muted-foreground">暂无聊天记录</p>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Performance */}
        <TabsContent value="performance">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Performance（绩效）</h3>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatCard icon={CheckCircle2} label="累计任务" value={agent.performance.totalTasks} color="text-blue-600" />
              <StatCard icon={CheckCircle2} label="成功任务" value={agent.performance.successTasks} color="text-green-600" />
              <StatCard icon={XCircle} label="失败任务" value={agent.performance.failedTasks} color="text-red-600" />
              <StatCard icon={Calendar} label="会议参与" value={agent.performance.meetingCount} color="text-purple-600" />
            </div>
            <div className="mt-6 rounded-lg bg-secondary/50 p-4">
              <p className="text-sm text-muted-foreground">
                最后活跃时间：{new Date(agent.lastActiveAt).toLocaleString('zh-CN')}
              </p>
            </div>
          </Card>
        </TabsContent>

        {/* Employment */}
        <TabsContent value="employment">
          <Card className="p-6">
            <h3 className="mb-4 text-lg font-semibold">Employment（雇佣信息）</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <InfoItem label="雇佣时间" value={new Date(agent.hiredAt).toLocaleString('zh-CN')} />
              <InfoItem label="部门" value={agent.department || '待上线'} />
              <InfoItem label="直属上级" value={agent.managerId === 'ceo' ? 'CEO' : agent.managerId || '待上线'} />
              <InfoItem label="状态" value={agent.status} />
              <InfoItem label="平台" value={agent.platform} />
              <InfoItem label="平台 Agent ID" value={agent.platformAgentId} />
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </PageWrapper>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-secondary/40 px-4 py-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  );
}

function SoulItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold text-primary">{label}</p>
      <p className="mt-1 text-sm text-muted-foreground">{value}</p>
    </div>
  );
}

function TaskStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    Pending: 'bg-yellow-100 text-yellow-700',
    Running: 'bg-blue-100 text-blue-700',
    Completed: 'bg-green-100 text-green-700',
    Failed: 'bg-red-100 text-red-700',
    Cancelled: 'bg-gray-100 text-gray-700',
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] || colors.Pending}`}>
      {status}
    </span>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: number; color: string }) {
  return (
    <div className="rounded-xl border bg-card p-4 text-center transition-all hover:shadow-soft">
      <Icon className={`mx-auto h-6 w-6 ${color}`} />
      <p className="mt-2 text-2xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
