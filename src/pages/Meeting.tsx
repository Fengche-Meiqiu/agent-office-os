/**
 * 会议室页面（V2 重构：自由讨论模式）
 *
 * 核心变更：
 * 1. 去掉固定 4 轮限制，改为自由讨论
 * 2. 开始会议按钮 → 所有 Agent 首次发言
 * 3. "让所有人发言"按钮 → askAll
 * 4. 点击任意 Agent 头像 → askAgent（指定谁发言）
 * 5. 主持人随时插话
 * 6. 结束会议按钮常驻，随时可点
 * 7. SSE 实时推送会议消息
 */
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Users, Send, Square, Play, UserCheck, MessageSquare, ArrowRight } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useOfficeAgents } from '@/hooks/useAgents';
import { useCreateTask } from '@/hooks/useTasks';
import {
  useMeetings,
  useMeeting,
  useCreateMeeting,
  useStartMeeting,
  useAskAll,
  useAskAgent,
  useFinishMeeting,
  useSendMeetingMessage,
} from '@/hooks/useMeetings';
import { useSSE } from '@/hooks/useSSE';

export default function Meeting() {
  const { id } = useParams<{ id: string }>();

  if (!id) {
    return <MeetingCreator />;
  }

  return <MeetingRoom meetingId={id} />;
}

// ===== 创建会议 =====
function MeetingCreator() {
  const navigate = useNavigate();
  const { data: agents = [] } = useOfficeAgents();
  const { data: allMeetings = [] } = useMeetings();
  const createMutation = useCreateMeeting();
  const [topic, setTopic] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // 找到进行中的会议（未结束的）
  const activeMeetings = allMeetings.filter((m) => m.status !== 'finished');

  const toggleAgent = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleCreate = () => {
    if (!topic.trim() || selectedIds.length < 2) return;
    createMutation.mutate(
      { topic, agentIds: selectedIds },
      {
        onSuccess: (meeting) => navigate(`/meeting/${meeting.id}`),
      }
    );
  };

  return (
    <PageWrapper className="mx-auto max-w-4xl space-y-6">
      {/* 进行中会议提示 */}
      {activeMeetings.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-3 w-3">
                <span className="absolute h-3 w-3 animate-ping rounded-full bg-yellow-400 opacity-75" />
                <span className="h-3 w-3 rounded-full bg-yellow-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-yellow-800">
                  有 {activeMeetings.length} 个会议正在进行中
                </p>
                <p className="text-xs text-yellow-600">点击下方按钮回到进行中的会议</p>
              </div>
            </div>
            <div className="flex gap-2">
              {activeMeetings.slice(0, 3).map((m) => (
                <Button
                  key={m.id}
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/meeting/${m.id}`)}
                  className="gap-1 border-yellow-300 bg-white text-yellow-800 hover:bg-yellow-100"
                >
                  {m.topic.length > 8 ? m.topic.slice(0, 8) + '...' : m.topic}
                  <ArrowRight className="h-3 w-3" />
                </Button>
              ))}
            </div>
          </div>
        </Card>
      )}

      <div>
        <h1 className="text-2xl font-bold font-display">会议室</h1>
        <p className="text-sm text-muted-foreground">
          选择 2~10 个员工，围绕主题进行自由讨论
        </p>
      </div>

      <Card className="p-6">
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium">会议主题</label>
            <Input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="例如：产品规划讨论"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">
              选择参会员工{' '}
              <span className="text-xs text-muted-foreground">
                （已选 {selectedIds.length} 人）
              </span>
            </label>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
              {agents.map((agent) => {
                const selected = selectedIds.includes(agent.id);
                return (
                  <button
                    key={agent.id}
                    onClick={() => toggleAgent(agent.id)}
                    className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all ${
                      selected ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
                    }`}
                  >
                    <AgentAvatar
                      src={agent.avatar}
                      name={agent.name}
                      status={agent.status}
                      size="sm"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{agent.name}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {agent.title}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <Button
            onClick={handleCreate}
            disabled={!topic.trim() || selectedIds.length < 2 || createMutation.isPending}
            className="w-full gap-2"
          >
            <Play className="h-4 w-4" />
            创建会议
          </Button>
        </div>
      </Card>
    </PageWrapper>
  );
}

// ===== 会议进行中/已结束 =====
function MeetingRoom({ meetingId }: { meetingId: string }) {
  const { data: meeting, isLoading } = useMeeting(meetingId);
  const { data: officeAgents = [] } = useOfficeAgents();
  const startMutation = useStartMeeting();
  const askAllMutation = useAskAll();
  const askAgentMutation = useAskAgent();
  const finishMutation = useFinishMeeting();
  const sendMessageMutation = useSendMeetingMessage();
  const createTaskMutation = useCreateTask();
  const [userInput, setUserInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // SSE 订阅会议消息（实时推送）
  const { isConnected } = useSSE('meetings', {
    meeting_message: (data) => {
      // 收到新消息时刷新会议数据
      if (data.meeting_id === meetingId) {
        // react-query 会自动重新拉取
      }
    },
    meeting_finished: (data) => {
      if (data.meeting_id === meetingId) {
        // 会议结束，刷新数据
      }
    },
  });

  // 新消息时自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [meeting?.messages]);

  if (isLoading) {
    return (
      <PageWrapper className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </PageWrapper>
    );
  }

  if (!meeting) {
    return (
      <PageWrapper className="flex h-full flex-col items-center justify-center text-center">
        <h2 className="text-xl font-semibold">会议不存在</h2>
        <Link to="/meeting" className="mt-4 text-primary hover:underline">
          创建新会议
        </Link>
      </PageWrapper>
    );
  }

  const isFinished = meeting.status === 'finished';
  const isCreated = meeting.status === 'created';
  const messages = meeting.messages || [];
  const messageCount = messages.length;

  return (
    <PageWrapper className="flex h-[calc(100vh-8rem)] gap-4">
      {/* 左侧：参会 Agent 列表（可点击让指定 Agent 发言） */}
      <Card className="flex w-64 flex-col overflow-hidden">
        <div className="border-b p-4">
          <h2 className="font-semibold">参会 Agent</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            点击头像让该 Agent 发言
          </p>
        </div>
        <ScrollArea className="flex-1 p-3">
          <div className="space-y-2">
            {meeting.agentIds.map((agentId) => (
              <AgentListItem
                key={agentId}
                agentId={agentId}
                disabled={isFinished || isCreated}
                onAsk={() =>
                  askAgentMutation.mutate({ meetingId, agentId })
                }
                isAsking={
                  askAgentMutation.isPending &&
                  askAgentMutation.variables?.agentId === agentId
                }
              />
            ))}
          </div>
        </ScrollArea>

        {/* SSE 连接状态 */}
        <div className="border-t p-3 text-xs">
          <span className="flex items-center gap-1.5">
            <span
              className={`h-2 w-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-gray-400'
              }`}
            />
            {isConnected ? '实时连接' : '未连接'}
          </span>
        </div>
      </Card>

      {/* 右侧：讨论区 */}
      <Card className="flex flex-1 flex-col overflow-hidden">
        {/* 顶部操作栏 */}
        <div className="flex items-center justify-between border-b px-5 py-3">
          <div>
            <h3 className="font-semibold">{meeting.topic}</h3>
            <p className="text-xs text-muted-foreground">
              {isFinished
                ? '已结束'
                : isCreated
                ? '点击「开始会议」启动讨论'
                : `已发言 ${messageCount} 条`}
            </p>
          </div>
          {!isFinished && (
            <div className="flex items-center gap-2">
              {isCreated && (
                <Button
                  onClick={() => startMutation.mutate(meeting.id)}
                  disabled={startMutation.isPending}
                  className="gap-1"
                >
                  <Play className="h-4 w-4" />
                  开始会议
                </Button>
              )}
              {!isCreated && (
                <Button
                  onClick={() => askAllMutation.mutate(meeting.id)}
                  disabled={askAllMutation.isPending}
                  variant="outline"
                  className="gap-1"
                >
                  <UserCheck className="h-4 w-4" />
                  让所有人发言
                </Button>
              )}
              <Button
                onClick={() => finishMutation.mutate(meeting.id)}
                disabled={finishMutation.isPending}
                variant="destructive"
                className="gap-1"
              >
                <Square className="h-4 w-4" />
                结束会议
              </Button>
            </div>
          )}
        </div>

        {/* 消息列表（扁平，无轮次分组） */}
        <ScrollArea className="flex-1 p-5" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
              <Users className="mb-3 h-12 w-12 opacity-30" />
              <p>
                {isCreated
                  ? '点击「开始会议」让所有 Agent 首次发言'
                  : '等待发言...'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {messages.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} />
              ))}
            </div>
          )}
        </ScrollArea>

        {/* 主持人输入区（会议未结束时始终可用） */}
        {!isFinished && (
          <div className="border-t px-5 py-3">
            <form
              className="flex items-center gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                if (!userInput.trim()) return;

                // 小白解释：如果主持人输入以 /task 开头，说明要布置正式任务。
                // 格式：/task agentName 任务内容
                // 例如：/task sanhuyi 分析泸州老窖
                if (userInput.trim().startsWith('/task')) {
                  const rest = userInput.trim().slice(5).trim();
                  const parts = rest.split(/\s+/);
                  if (parts.length < 2) {
                    alert('格式不对，请使用：/task 员工名 任务内容');
                    return;
                  }
                  const agentName = parts[0];
                  const taskContent = parts.slice(1).join(' ');
                  const targetAgent = officeAgents.find((a) => a.name === agentName);
                  if (!targetAgent) {
                    alert(`找不到员工 "${agentName}"，请检查名字是否正确`);
                    return;
                  }
                  if (!meeting.agentIds.includes(targetAgent.id)) {
                    alert(`"${agentName}" 不在当前会议中`);
                    return;
                  }
                  createTaskMutation.mutate(
                    {
                      agentId: targetAgent.id,
                      title: taskContent,
                      content: taskContent,
                    },
                    { onSuccess: () => setUserInput('') }
                  );
                  return;
                }

                sendMessageMutation.mutate(
                  { id: meeting.id, content: userInput },
                  { onSuccess: () => setUserInput('') }
                );
              }}
            >
              <Input
                placeholder="作为主持人插话...（/task 员工名 内容 可创建任务）"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                className="flex-1"
              />
              <Button
                type="submit"
                size="icon"
                disabled={
                  !userInput.trim() ||
                  sendMessageMutation.isPending ||
                  createTaskMutation.isPending
                }
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        )}
      </Card>

      {/* 会议结果（已结束时显示） */}
      {isFinished && (
        <Card className="flex w-80 flex-col overflow-hidden">
          <div className="border-b p-4">
            <h2 className="font-semibold">会议结果</h2>
          </div>
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              <div>
                <h4 className="mb-1 text-sm font-semibold">会议纪要</h4>
                <p className="whitespace-pre-wrap text-xs text-muted-foreground">
                  {meeting.summary}
                </p>
              </div>
              {meeting.decisions && meeting.decisions.length > 0 && (
                <div>
                  <h4 className="mb-1 text-sm font-semibold">决策建议</h4>
                  <ul className="space-y-1">
                    {meeting.decisions.map((d, i) => (
                      <li key={i} className="text-xs text-muted-foreground">
                        • {d}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {meeting.actions && meeting.actions.length > 0 && (
                <div>
                  <h4 className="mb-1 text-sm font-semibold">行动项</h4>
                  <ul className="space-y-1">
                    {meeting.actions.map((a, i) => (
                      <li key={i} className="text-xs text-muted-foreground">
                        • {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </ScrollArea>
        </Card>
      )}
    </PageWrapper>
  );
}

// ===== 单条消息气泡 =====
function MessageBubble({ message }: { message: import('@/types').MeetingMessage }) {
  const isUser = message.role === 'user';
  const name = isUser ? '主持人' : message.agentName || 'Unknown';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <AgentAvatar name={name} size="sm" showStatus={false} />
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary'
        }`}
      >
        <p
          className={`mb-1 text-xs font-medium ${
            isUser ? 'text-primary-foreground/80' : 'text-muted-foreground'
          }`}
        >
          {name}
        </p>
        {message.content}
      </div>
    </div>
  );
}

// ===== 参会 Agent 列表项（可点击触发发言） =====
function AgentListItem({
  agentId,
  disabled,
  onAsk,
  isAsking,
}: {
  agentId: string;
  disabled: boolean;
  onAsk: () => void;
  isAsking: boolean;
}) {
  const { data: agents } = useOfficeAgents();
  const found = agents?.find((a) => a.id === agentId);
  if (!found) return null;

  return (
    <button
      onClick={onAsk}
      disabled={disabled || isAsking}
      className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
    >
      <AgentAvatar
        src={found.avatar}
        name={found.name}
        status={found.status}
        size="sm"
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{found.name}</p>
        <StatusBadge status={found.status} size="sm" />
      </div>
      {isAsking && (
        <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
      )}
      {!isAsking && !disabled && (
        <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
      )}
    </button>
  );
}
