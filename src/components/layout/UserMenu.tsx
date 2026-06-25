import { Link } from 'react-router-dom';
import { User, Settings, LogOut } from 'lucide-react';
import { Card } from '@/components/ui/card';

/**
 * 用户下拉菜单
 * 点击右上角头像/角色后弹出，提供常用入口（V1 中退出登录为占位）
 */
export function UserMenu() {
  const menuItems = [
    { label: '个人设置', icon: User, to: '/settings' },
    { label: '系统设置', icon: Settings, to: '/settings' },
    { label: '退出登录', icon: LogOut, to: '#', disabled: true },
  ];

  return (
    <Card className="w-48 overflow-hidden p-0 shadow-card animate-in fade-in zoom-in-95 duration-200">
      <div className="divide-y">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const content = (
            <>
              <Icon className="h-4 w-4" />
              <span className={item.disabled ? 'opacity-50' : ''}>{item.label}</span>
            </>
          );

          return (
            <div key={item.label}>
              {item.disabled ? (
                <button
                  disabled
                  className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-muted-foreground"
                >
                  {content}
                </button>
              ) : (
                <Link
                  to={item.to}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm transition-colors hover:bg-accent"
                >
                  {content}
                </Link>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
