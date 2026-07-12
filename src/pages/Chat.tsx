import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Send, Paperclip, Smile, Phone, Video, MoreVertical, User, Lightbulb } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { AgentAvatar } from '@/components/shared/AgentAvatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { MarkdownRenderer } from '@/components/chat/MarkdownRenderer';
import { useOfficeAgents } from '@/hooks/useAgents';
import { useChatMessages, useSendMessage } from '@/hooks/useChats';
import { useCreateTask } from '@/hooks/useTasks';

export default function Chat() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [input, setInput] = useState('');
  const [taskFeedback, setTaskFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: agents = [] } = useOfficeAgents();
  const { data: messages = [], isLoading } = useChatMessages(id);
  const sendMutation = useSendMessage();
  const createTaskMutation = useCreateTask();

  const selectedAgent = agents.find((a) => a.id === id) || agents[0];

  // 如果没有 id 或 id 无效，默认跳转到第一个 Agent
  useEffect(() => {
    if (!id && agents.length > 0) {
      navigate(`/chat/${agents[0].id}`, { replace: true });
    }
  }, [id, agents, navigate]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || !selectedAgent) return;

    // 小白解释：如果消息以 /task 开头，说明用户想布置正式任务，
    // 不走聊天接口，而是调用任务创建接口派发给 Hermes。
    // 例如：/task 分析泸州老窖
    if (input.trim().startsWith('/task')) {
      const rawContent = input.trim();
      const taskContent = rawContent.slice(5).trim();
      const title = taskContent || '未命名任务';

      // 先把 /task 指令显示在聊天界面，让用户知道自己发过了
      const tempMsg = {
        id: `taskcmd_${Date.now()}`,
        agentId: selectedAgent.id,
        role: 'user' as const,
        content: rawContent,
        timestamp: new Date().toISOString(),
      };
      queryClient.setQueryData(['chatMessages', selectedAgent.id], (old: any[]) => {
        return [...(old || []), tempMsg];
      });

      createTaskMutation.mutate(
        {
          agentId: selectedAgent.id,
          title,
          content: taskContent,
        },
        {
          onSuccess: () => {
            // 小白解释：不用 alert 阻塞，改用页面内提示，避免 React 渲染死循环。
            setTaskFeedback({
              type: 'success',
              message: `任务「${title}」已创建，请在任务中心查看执行进度。完成后 Hermes 会通过 Webhook 把结果推回来。`,
            });
            setTimeout(() => setTaskFeedback(null), 5000);
          },
          onError: (err) => {
            const msg = err instanceof Error ? err.message : '未知错误';
            setTaskFeedback({ type: 'error', message: `任务创建失败：${msg}` });
            setTimeout(() => setTaskFeedback(null), 5000);
          },
        }
      );
      setInput('');
      return;
    }

    sendMutation.mutate({ agentId: selectedAgent.id, content: input });
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <PageWrapper className="flex h-[calc(100vh-8rem)] gap-4">
      {/* 左侧 Agent 列表 */}
      <Card className="hidden w-64 flex-col overflow-hidden md:flex">
        <div className="border-b p-4">
          <h2 className="font-semibold">聊天列表</h2>
        </div>
        <ScrollArea className="flex-1">
          <div className="space-y-1 p-2">
            {agents.map((agent) => (
              <Link
                key={agent.id}
                to={`/chat/${agent.id}`}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors ${
                  selectedAgent?.id === agent.id
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                }`}
              >
                <AgentAvatar src={agent.avatar} name={agent.name} status={agent.status} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{agent.name}</p>
                  <p className="truncate text-xs text-muted-foreground">{agent.title}</p>
                </div>
              </Link>
            ))}
          </div>
        </ScrollArea>
      </Card>

      {/* 右侧聊天窗口 */}
      <Card className="flex flex-1 flex-col overflow-hidden">
        {selectedAgent ? (
          <>
            {/* 顶部 Agent 信息 */}
            <div className="flex items-center justify-between border-b px-5 py-3">
              <div className="flex items-center gap-3">
                <AgentAvatar src={selectedAgent.avatar} name={selectedAgent.name} status={selectedAgent.status} size="md" />
                <div>
                  <h3 className="font-semibold">{selectedAgent.name}</h3>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={selectedAgent.status} size="sm" />
                    <span className="text-xs text-muted-foreground">{selectedAgent.title}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon">
                  <Phone className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon">
                  <Video className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* 聊天记录 */}
            <ScrollArea className="flex-1 p-5">
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((msg, index) => {
                    // 小白解释：Agent 回复上面一条用户消息时，把用户原话记下来，
                    // 这样 suggestTask 提示可以一键帮用户填入 /task 指令。
                    const prevUserContent =
                      msg.role === 'agent' &&
                      index > 0 &&
                      messages[index - 1].role === 'user'
                        ? messages[index - 1].content
                        : '';

                    return (
                      <div
                        key={msg.id}
                        className={`flex flex-col gap-2 ${
                          msg.role === 'user' ? 'items-end' : 'items-start'
                        }`}
                      >
                        <div
                          className={`flex gap-3 ${
                            msg.role === 'user' ? 'flex-row-reverse' : ''
                          }`}
                        >
                          {msg.role === 'agent' ? (
                            <AgentAvatar
                              src={selectedAgent.avatar}
                              name={selectedAgent.name}
                              status={selectedAgent.status}
                              size="sm"
                              showStatus={false}
                            />
                          ) : (
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs text-white">
                              我
                            </div>
                          )}
                          <div
                            className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                              msg.role === 'user'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-secondary'
                            }`}
                          >
                            {msg.role === 'agent' ? (
                              <MarkdownRenderer content={msg.content} />
                            ) : (
                              msg.content
                            )}
                          </div>
                        </div>

                        {/* Agent 建议用 /task 模式时的提示卡片 */}
                        {msg.role === 'agent' && msg.suggestTask && (
                          <div className="max-w-[80%] rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm shadow-sm">
                            <div className="flex items-start gap-2">
                              <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                              <div className="flex-1">
                                <p className="font-medium text-amber-800">
                                  分析类问题建议用任务模式
                                </p>
                                <p className="mt-1 text-amber-700">
                                  这类问题需要查数据、做计算，用 /task
                                  异步派发可以生成完整成果并存档。
                                </p>
                                {prevUserContent && (
                                  <button
                                    onClick={() =>
                                      setInput(`/task ${prevUserContent}`)
                                    }
                                    className="mt-2 rounded-md bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-800 hover:bg-amber-200"
                                  >
                                    帮我填入 /task 指令
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {/* Agent 思考中指示器 */}
                  {sendMutation.isPending && (
                    <div className="flex gap-3">
                      <AgentAvatar
                        src={selectedAgent.avatar}
                        name={selectedAgent.name}
                        status={selectedAgent.status}
                        size="sm"
                        showStatus={false}
                      />
                      <div className="rounded-2xl bg-secondary px-4 py-2.5 text-sm shadow-sm">
                        <span className="flex items-center gap-2 text-muted-foreground">
                          <span className="flex gap-0.5">
                            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" style={{ animationDelay: '0ms' }} />
                            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" style={{ animationDelay: '150ms' }} />
                            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" style={{ animationDelay: '300ms' }} />
                          </span>
                          {selectedAgent.name} 思考中...
                        </span>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>

            {/* 任务创建反馈提示 */}
            {taskFeedback && (
              <div
                className={`mx-4 mb-2 rounded-lg px-4 py-2 text-sm ${
                  taskFeedback.type === 'success'
                    ? 'bg-green-50 text-green-800 border border-green-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {taskFeedback.message}
              </div>
            )}

            {/* 输入框 */}
            <div className="border-t p-4">
              <div className="flex items-end gap-2 rounded-2xl border bg-background p-2">
                <Button variant="ghost" size="icon" className="shrink-0">
                  <Paperclip className="h-5 w-5 text-muted-foreground" />
                </Button>
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入消息...（/task 开头可创建任务）"
                  className="min-h-[44px] flex-1 resize-none border-0 bg-transparent focus-visible:ring-0"
                />
                <Button variant="ghost" size="icon" className="shrink-0">
                  <Smile className="h-5 w-5 text-muted-foreground" />
                </Button>
                <Button
                  size="icon"
                  className="shrink-0 rounded-xl"
                  onClick={handleSend}
                  disabled={!input.trim() || sendMutation.isPending || createTaskMutation.isPending}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center text-muted-foreground">
            <User className="h-12 w-12 mb-3 opacity-30" />
            <p>请选择一个 Agent 开始聊天</p>
          </div>
        )}
      </Card>
    </PageWrapper>
  );
}
