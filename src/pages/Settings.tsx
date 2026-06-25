import { useState } from 'react';
import { Moon, Sun, Bell, Database, Trash2, Globe, Shield } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { useTheme } from '@/hooks/useTheme';
import { resetMockData } from '@/lib/mockApi';

/**
 * 系统设置页面
 * 提供外观主题、通知、语言等常用设置，以及重置模拟数据的功能
 */
export default function Settings() {
  const { theme, toggleTheme, isDark } = useTheme();
  const [notifications, setNotifications] = useState(true);
  const [language, setLanguage] = useState<'zh' | 'en'>('zh');
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

  /**
   * 重置所有模拟数据并刷新页面
   * 这样 LocalStorage 会恢复到初始种子数据
   */
  const handleReset = () => {
    resetMockData();
    window.location.reload();
  };

  return (
    <PageWrapper className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold font-display">系统设置</h1>
        <p className="text-sm text-muted-foreground">管理界面主题、通知偏好与本地数据</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 外观设置 */}
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              {isDark ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
            </div>
            <div>
              <h3 className="font-semibold">外观主题</h3>
              <p className="text-xs text-muted-foreground">切换浅色 / 深色模式</p>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <span className="text-sm">当前主题：{isDark ? '深色模式' : '浅色模式'}</span>
            <Button variant="outline" size="sm" onClick={toggleTheme}>
              {isDark ? '切换到浅色' : '切换到深色'}
            </Button>
          </div>
        </Card>

        {/* 通知设置 */}
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bell className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold">消息通知</h3>
              <p className="text-xs text-muted-foreground">是否接收任务、会议等提醒</p>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg border p-3">
            <span className="text-sm">启用通知</span>
            <button
              onClick={() => setNotifications((v) => !v)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                notifications ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <span
                className={`absolute top-1 left-1 h-4 w-4 rounded-full bg-white transition-transform ${
                  notifications ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </Card>

        {/* 语言设置 */}
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold">语言</h3>
              <p className="text-xs text-muted-foreground">选择界面显示语言（V1 仅展示）</p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant={language === 'zh' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setLanguage('zh')}
            >
              简体中文
            </Button>
            <Button
              variant={language === 'en' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setLanguage('en')}
            >
              English
            </Button>
          </div>
        </Card>

        {/* 数据管理 */}
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-semibold">本地数据</h3>
              <p className="text-xs text-muted-foreground">重置为初始演示数据</p>
            </div>
          </div>

          <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive" size="sm" className="gap-2">
                <Trash2 className="h-4 w-4" />
                重置模拟数据
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>确认重置数据？</DialogTitle>
                <DialogDescription>
                  这会把所有本地存储的 Agent、任务、会议等数据恢复到初始演示状态，无法撤销。
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setResetDialogOpen(false)}>
                  取消
                </Button>
                <Button variant="destructive" onClick={handleReset}>
                  确认重置
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </Card>
      </div>

      {/* 版本信息 */}
      <div className="flex items-center justify-between rounded-lg border p-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4" />
          <span>Agent Office OS</span>
        </div>
        <Badge variant="outline">V1.0.0</Badge>
      </div>
    </PageWrapper>
  );
}
