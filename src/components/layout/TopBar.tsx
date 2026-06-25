import { useState, useRef, useEffect } from 'react';
import { Bell, Search, ChevronDown } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Avatar } from '@/components/ui/avatar';
import { NotificationPanel } from './NotificationPanel';
import { UserMenu } from './UserMenu';

/**
 * 顶部栏
 * 包含全局搜索、通知面板触发器、用户菜单触发器
 */
export function TopBar() {
  const [notifyOpen, setNotifyOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const notifyRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  // 点击面板外部时自动关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notifyRef.current && !notifyRef.current.contains(event.target as Node)) {
        setNotifyOpen(false);
      }
      if (userRef.current && !userRef.current.contains(event.target as Node)) {
        setUserOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      {/* 左侧搜索 */}
      <div className="flex w-full max-w-md items-center gap-2">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索 Agent / 任务 / 会议"
            className="pl-9 bg-secondary/50 border-0 focus-visible:ring-primary/30"
          />
        </div>
      </div>

      {/* 右侧用户信息 */}
      <div className="flex items-center gap-4">
        {/* 通知 */}
        <div ref={notifyRef} className="relative">
          <button
            onClick={() => setNotifyOpen((v) => !v)}
            className="relative rounded-full p-2 text-muted-foreground hover:bg-accent"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-destructive" />
          </button>
          {notifyOpen && (
            <div className="absolute right-0 top-full z-50 mt-2">
              <NotificationPanel onClose={() => setNotifyOpen(false)} />
            </div>
          )}
        </div>

        {/* 用户菜单 */}
        <div ref={userRef} className="relative flex items-center gap-3 pl-4 border-l">
          <button
            onClick={() => setUserOpen((v) => !v)}
            className="flex items-center gap-2 text-right hover:opacity-80"
          >
            <div className="hidden sm:block">
              <p className="text-sm font-medium">产品负责人</p>
              <p className="text-xs text-status-online">在线</p>
            </div>
            <Avatar src="https://api.dicebear.com/7.x/avataaars/svg?seed=Manager&backgroundColor=c0aede" fallback="PM" />
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </button>
          {userOpen && (
            <div className="absolute right-0 top-full z-50 mt-2">
              <UserMenu />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
