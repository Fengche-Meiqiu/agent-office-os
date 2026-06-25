import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Send, Paperclip, Smile, Phone, Video, MoreVertical, User } from 'lucide-react';
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

export default function Chat() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: agents = [] } = useOfficeAgents();
  const { data: messages = [], isLoading } = useChatMessages(id);
  const sendMutation = useSendMessage();

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
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
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
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>

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
                  placeholder="输入消息..."
                  className="min-h-[44px] flex-1 resize-none border-0 bg-transparent focus-visible:ring-0"
                />
                <Button variant="ghost" size="icon" className="shrink-0">
                  <Smile className="h-5 w-5 text-muted-foreground" />
                </Button>
                <Button
                  size="icon"
                  className="shrink-0 rounded-xl"
                  onClick={handleSend}
                  disabled={!input.trim() || sendMutation.isPending}
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
