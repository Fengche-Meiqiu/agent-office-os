import { useState } from 'react';
import { Moon, Sun, Bell, Globe, Shield } from 'lucide-react';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useTheme } from '@/hooks/useTheme';
import { useLanguage } from '@/i18n';

/**
 * 系统设置页面（V2：移除重置模拟数据按钮）
 *
 * 小白解释：这里可以切换深色/浅色模式、开关通知、选语言。
 * V2 版本不再有"重置模拟数据"按钮，因为最终交付不含测试数据。
 */
export default function Settings() {
  const { toggleTheme, isDark } = useTheme();
  const [notifications, setNotifications] = useState(true);
  const { locale, setLocale } = useLanguage();

  return (
    <PageWrapper className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-2xl font-bold font-display">系统设置</h1>
        <p className="text-sm text-muted-foreground">管理界面主题与通知偏好</p>
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
              <p className="text-xs text-muted-foreground">选择界面显示语言</p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant={locale === 'zh-CN' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setLocale('zh-CN')}
            >
              简体中文
            </Button>
            <Button
              variant={locale === 'en-US' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setLocale('en-US')}
            >
              English
            </Button>
          </div>
        </Card>
      </div>

      {/* 版本信息 */}
      <div className="flex items-center justify-between rounded-lg border p-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4" />
          <span>Agent Office OS</span>
        </div>
        <Badge variant="outline">V2.0.0</Badge>
      </div>
    </PageWrapper>
  );
}

