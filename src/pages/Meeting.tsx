import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Users, MessageSquare, CheckCircle2, ArrowRight, Sparkles, Mic, Video, Send } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useOfficeAgents } from '@/hooks/useAgents';
import { useMeeting, useCreateMeeting, useNextRound, useFinishMeeting, useSendMeetingMessage } from '@/hooks/useMeetings';

const roundNames = ['独立意见', '交叉评论', '达成共识', '形成结论'];

export default function Meeting() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  if (!id) {
    return <MeetingCreator />;
  }

  return <MeetingRoom meetingId={id} />;
}

// 创建会议
function MeetingCreator() {
  const navigate = useNavigate();
  const { data: agents = [] } = useOfficeAgents();
  const createMutation = useCreateMeeting();
  const [topic, setTopic] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

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
      <div>
        <h1 className="text-2xl font-bold font-display">会议室</h1>
        <p className="text-sm text-muted-foreground">选择 2~10 个员工，围绕主题进行多轮讨论</p>
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
              选择参会员工 <span className="text-xs text-muted-foreground">（已选 {selectedIds.length} 人）</span>
            </label>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
              {agents.map((agent) => {
                const selected = selectedIds.includes(agent.id);
                return (
                  <button
                    key={agent.id}
                    onClick={() => toggleAgent(agent.id)}
                    className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all ${
                      selected
                        ? 'border-primary bg-primary/5'
                        : 'hover:border-primary/50'
                    }`}
                  >
                    <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="sm" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{agent.name}</p>
                      <p className="truncate text-xs text-muted-foreground">{agent.title}</p>
                    </div>
                    {selected && <CheckCircle2 className="h-4 w-4 shrink-0 text-primary" />}
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
            <Sparkles className="h-4 w-4" />
            开始会议
          </Button>
        </div>
      </Card>
    </PageWrapper>
  );
}

// 会议进行中/已结束
function MeetingRoom({ meetingId }: { meetingId: string }) {
  const { data: meeting, isLoading } = useMeeting(meetingId);
  const nextRoundMutation = useNextRound();
  const finishMutation = useFinishMeeting();
  const sendMessageMutation = useSendMeetingMessage();
  const [userInput, setUserInput] = useState('');

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
        <Link to="/meeting" className="mt-4 text-primary hover:underline">创建新会议</Link>
      </PageWrapper>
    );
  }

  const currentRound = meeting.rounds.length;
  const isFinished = meeting.status === 'finished';

  return (
    <PageWrapper className="flex h-[calc(100vh-8rem)] gap-4">
      {/* 左侧参会 Agent */}
      <Card className="flex w-64 flex-col overflow-hidden">
        <div className="border-b p-4">
          <h2 className="font-semibold">参会 Agent</h2>
        </div>
        <ScrollArea className="flex-1 p-3">
          <div className="space-y-2">
            {meeting.agentIds.map((agentId) => (
              <AgentListItem key={agentId} agentId={agentId} />
            ))}
          </div>
        </ScrollArea>
      </Card>

      {/* 右侧讨论区 */}
      <Card className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <div>
            <h3 className="font-semibold">{meeting.topic}</h3>
            <p className="text-xs text-muted-foreground">
              {isFinished ? '已结束' : currentRound > 0 ? `Round ${currentRound} / 4` : '准备中'}
            </p>
          </div>
          {!isFinished && (
            <div className="flex items-center gap-2">
              {currentRound < 4 && (
                <Button
                  onClick={() => nextRoundMutation.mutate(meeting.id)}
                  disabled={nextRoundMutation.isPending}
                  className="gap-1"
                >
                  {currentRound === 0 ? '开始第一轮' : '下一轮'}
                  <ArrowRight className="h-4 w-4" />
                </Button>
              )}
              {currentRound >= 4 && (
                <Button onClick={() => finishMutation.mutate(meeting.id)} disabled={finishMutation.isPending}>
                  结束会议
                </Button>
              )}
            </div>
          )}
        </div>

        <ScrollArea className="flex-1 p-5">
          {meeting.rounds.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
              <Users className="h-12 w-12 mb-3 opacity-30" />
              <p>点击「开始第一轮」启动会议讨论</p>
            </div>
          ) : (
            <div className="space-y-6">
              {meeting.rounds.map((round) => (
                <div key={round.round}>
                  <div className="mb-3 flex items-center gap-2">
                    <Badge variant="secondary">Round {round.round}</Badge>
                    <span className="text-sm font-medium">{round.name}</span>
                  </div>
                  <div className="space-y-3">
                    {round.messages.map((msg, idx) => (
                      <MessageBubble key={idx} message={msg} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* 主持人输入区：会议进行中且已开始第一轮时显示 */}
        {!isFinished && currentRound > 0 && (
          <div className="border-t px-5 py-3">
            <form
              className="flex items-center gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                if (!userInput.trim()) return;
                sendMessageMutation.mutate(
                  { id: meeting.id, content: userInput },
                  { onSuccess: () => setUserInput('') }
                );
              }}
            >
              <Input
                placeholder="作为主持人插话..."
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                className="flex-1"
              />
              <Button
                type="submit"
                size="icon"
                disabled={!userInput.trim() || sendMessageMutation.isPending}
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        )}

        {/* 底部状态栏 */}
        <div className="border-t px-5 py-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Mic className="h-3 w-3" /> 语音就绪
              </span>
              <span className="flex items-center gap-1">
                <Video className="h-3 w-3" /> 文字会议
              </span>
            </div>
            <span>创建于 {new Date(meeting.createdAt).toLocaleString('zh-CN')}</span>
          </div>
        </div>
      </Card>

      {/* 会议结果 */}
      {isFinished && (
        <Card className="flex w-80 flex-col overflow-hidden">
          <div className="border-b p-4">
            <h2 className="font-semibold">会议结果</h2>
          </div>
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              <div>
                <h4 className="mb-1 text-sm font-semibold">会议纪要</h4>
                <p className="text-xs text-muted-foreground">{meeting.summary}</p>
              </div>
              <div>
                <h4 className="mb-1 text-sm font-semibold">决策建议</h4>
                <ul className="space-y-1">
                  {meeting.decisions?.map((d, i) => (
                    <li key={i} className="text-xs text-muted-foreground">• {d}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="mb-1 text-sm font-semibold">行动项</h4>
                <ul className="space-y-1">
                  {meeting.actions?.map((a, i) => (
                    <li key={i} className="text-xs text-muted-foreground">• {a}</li>
                  ))}
                </ul>
              </div>
            </div>
          </ScrollArea>
        </Card>
      )}
    </PageWrapper>
  );
}

// 单条会议消息气泡：区分用户消息和 Agent 消息
function MessageBubble({ message }: { message: import('@/types').MeetingMessage }) {
  const isUser = message.role === 'user';
  const name = isUser ? '我' : message.agentName || 'Unknown';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <AgentAvatar name={name} size="sm" showStatus={false} />
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary'
        }`}
      >
        <p className={`mb-1 text-xs font-medium ${isUser ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
          {name}
        </p>
        {message.content}
      </div>
    </div>
  );
}

function AgentListItem({ agentId }: { agentId: string }) {
  const { data: agent } = useOfficeAgents();
  const found = agent?.find((a) => a.id === agentId);
  if (!found) return null;

  return (
    <Link to={`/profile/${found.id}`} className="flex items-center gap-3 rounded-lg p-2 hover:bg-accent">
      <AgentAvatar src={found.avatar} name={found.name} status={found.status} size="sm" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{found.name}</p>
        <StatusBadge status={found.status} size="sm" />
      </div>
    </Link>
  );
}
