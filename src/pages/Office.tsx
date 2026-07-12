import { Link } from 'react-router-dom';
import { Plus, Video, MessageSquare, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { StatsBar } from '@/components/office/StatsBar';
import { AgentCard } from '@/components/office/AgentCard';
import { ActivityFeed } from '@/components/office/ActivityFeed';
import { useOfficeAgents } from '@/hooks/useAgents';
import { useTasks } from '@/hooks/useTasks';
import { useChatMessages } from '@/hooks/useChats';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import type { OfficeAgent } from '@/types';

export default function Office() {
  const { data: agents = [], isLoading: agentsLoading } = useOfficeAgents();
  const { data: tasks = [] } = useTasks();

  // 计算统计数据
  const total = agents.length;
  const online = agents.filter((a) => a.status === 'ONLINE').length;
  const working = agents.filter((a) => a.status === 'WORKING').length;
  const completedToday = tasks.filter((t) => t.status === 'Completed').length;
  const running = tasks.filter((t) => t.status === 'Running').length;

  // 为每个 Agent 匹配今日任务
  const agentTodayTasks: Record<string, string> = {};
  agents.forEach((agent) => {
    const task = tasks.find((t) => t.agentId === agent.id);
    agentTodayTasks[agent.id] = task ? task.name : '暂无任务';
  });

  // 首页展示第一个 Agent 的预览
  const featuredAgent = agents[0];

  return (
    <PageWrapper className="space-y-6">
      {/* 页面标题 */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold font-display">虚拟办公室</h1>
          <p className="text-sm text-muted-foreground">
            管理你的 AI Agent 团队，查看工作状态，协作完成任务
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/meeting">
            <Button variant="outline" className="gap-2">
              <Video className="h-4 w-4" />
              创建会议室
            </Button>
          </Link>
          <Link to="/marketplace">
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              添加 Agent
            </Button>
          </Link>
        </div>
      </div>

      {/* 统计栏 */}
      <StatsBar
        total={total}
        online={online}
        working={working}
        completedToday={completedToday}
        running={running}
      />

      {/* 主内容区 */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* 左侧工位区 */}
        <div className="xl:col-span-2 space-y-6">
          <Card className="p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold">Agent 工位</h2>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>全部区域</span>
              </div>
            </div>

            {agentsLoading ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-48 animate-pulse rounded-xl bg-muted" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    todayTask={agentTodayTasks[agent.id]}
                  />
                ))}
                {/* 添加新 Agent 占位卡片 */}
                <Link to="/marketplace">
                  <Card className="flex h-full min-h-[220px] flex-col items-center justify-center gap-3 p-4 text-muted-foreground transition-all hover:border-primary hover:text-primary cursor-pointer">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/40">
                      <Plus className="h-6 w-6" />
                    </div>
                    <span className="text-sm font-medium">邀请新 Agent 入驻</span>
                  </Card>
                </Link>
              </div>
            )}
          </Card>

          {/* 底部 Alice 预览 + 聊天预览 */}
          {featuredAgent && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <AgentAvatar src={featuredAgent.avatar} name={featuredAgent.name} status={featuredAgent.status} size="xl" />
                    <div>
                      <h3 className="text-lg font-semibold">
                        {featuredAgent.name}（{featuredAgent.title}）
                        <StatusBadge status={featuredAgent.status} size="sm" className="ml-2" />
                      </h3>
                      <div className="mt-3 flex gap-4 text-sm">
                        <Link to={`/profile/${featuredAgent.id}`} className="text-primary hover:underline">基本信息</Link>
                        <Link to={`/profile/${featuredAgent.id}`} className="text-primary hover:underline">能力 & 技能</Link>
                      </div>
                    </div>
                  </div>
                  <Link to={`/chat/${featuredAgent.id}`}>
                    <Button variant="ghost" size="icon">
                      <MessageSquare className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>

                <Separator className="my-4" />

                <div className="space-y-3">
                  <div>
                    <p className="text-xs font-semibold text-primary mb-1">Soul（人格）</p>
                    <p className="text-sm text-muted-foreground line-clamp-2">{featuredAgent.soul?.description || '暂无描述'}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-primary mb-1">Skills（技能）</p>
                    <div className="flex flex-wrap gap-1.5">
                      {(featuredAgent.skills || []).slice(0, 5).map((skill) => (
                        <span key={skill} className="rounded-md bg-secondary px-2 py-0.5 text-xs">{skill}</span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-primary mb-1">Tools（工具）</p>
                    <div className="flex flex-wrap gap-1.5">
                      {(featuredAgent.tools || []).slice(0, 4).map((tool) => (
                        <span key={tool} className="rounded-md bg-secondary px-2 py-0.5 text-xs">{tool}</span>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground pt-2">来源：{featuredAgent.platform} · 加入时间：{featuredAgent.hiredAt.slice(0, 10)}</p>
                </div>
              </Card>

              <ChatPreviewCard agent={featuredAgent} />
            </div>
          )}
        </div>

        {/* 右侧实时任务流 */}
        <div className="h-[calc(100vh-12rem)] min-h-[500px]">
          <ActivityFeed />
        </div>
      </div>
    </PageWrapper>
  );
}

/**
 * 聊天预览卡片
 * 展示与当前 Agent 的最近几条真实聊天记录，不再用硬编码示例数据
 */
function ChatPreviewCard({ agent }: { agent: OfficeAgent }) {
  const { data: messages = [], isLoading } = useChatMessages(agent.id);
  const recentMessages = messages.slice(-3).reverse();

  return (
    <Card className="p-5 flex flex-col">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">与 {agent.name} 对话</h3>
        <Link to={`/chat/${agent.id}`}>
          <Button variant="ghost" size="icon">
            <MessageSquare className="h-4 w-4" />
          </Button>
        </Link>
      </div>
      <div className="flex-1 rounded-lg bg-secondary/30 p-3">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-md bg-muted" />
            ))}
          </div>
        ) : recentMessages.length > 0 ? (
          <div className="space-y-3">
            {recentMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                {msg.role === 'agent' ? (
                  <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="sm" showStatus={false} />
                ) : (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs text-white">
                    我
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-lg px-3 py-2 text-sm shadow-sm ${
                    msg.role === 'user' ? 'bg-primary text-white' : 'bg-white'
                  }`}
                >
                  {msg.content.length > 60 ? msg.content.slice(0, 60) + '...' : msg.content}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">暂无对话，点击右侧图标开始聊天</p>
        )}
      </div>
    </Card>
  );
}
