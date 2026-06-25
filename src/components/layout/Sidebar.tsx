import { NavLink } from 'react-router-dom';
import {
  LayoutGrid,
  Store,
  MessageSquare,
  CheckSquare,
  FolderOpen,
  Users,
  Network,
  Settings,
  Wrench,
  BarChart3,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

const mainNavItems: NavItem[] = [
  { label: '办公室', path: '/', icon: LayoutGrid },
  { label: '会议室', path: '/meeting', icon: Users },
  { label: '任务中心', path: '/tasks', icon: CheckSquare },
  { label: 'Agent 管理', path: '/marketplace', icon: Store },
  { label: '聊天中心', path: '/chat', icon: MessageSquare },
  { label: '成果中心', path: '/outputs', icon: FolderOpen },
  { label: '组织架构', path: '/organization', icon: Network },
];

const bottomNavItems: NavItem[] = [
  { label: '工具中心', path: '/tools', icon: Wrench },
  { label: '数据看板', path: '/dashboard', icon: BarChart3 },
  { label: '系统设置', path: '/settings', icon: Settings },
];

function NavItemRenderer({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.path}
      end={item.path === '/'}
      className={({ isActive }) =>
        cn(
          'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
          'hover:bg-accent hover:text-accent-foreground',
          isActive
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground'
        )
      }
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </NavLink>
  );
}

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={cn(
        'relative flex h-screen flex-col border-r bg-card transition-all duration-300',
        sidebarCollapsed ? 'w-[72px]' : 'w-[220px]'
      )}
    >
      {/* Logo 区域 */}
      <div className="flex h-16 items-center gap-3 border-b px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-white">
          <LayoutGrid className="h-5 w-5" />
        </div>
        {!sidebarCollapsed && (
          <div className="flex flex-col">
            <span className="text-sm font-bold leading-tight">Agent Office</span>
            <span className="text-[10px] text-muted-foreground leading-tight">AI 虚拟办公系统</span>
          </div>
        )}
      </div>

      {/* 主导航 */}
      <nav className="flex-1 space-y-1 overflow-auto p-3">
        {mainNavItems.map((item) => (
          <NavItemRenderer key={item.path} item={item} collapsed={sidebarCollapsed} />
        ))}

        {!sidebarCollapsed && (
          <div className="pt-4 pb-2">
            <p className="px-3 text-xs font-semibold text-muted-foreground">我的收藏</p>
          </div>
        )}
        {sidebarCollapsed && <div className="my-3 border-t" />}
        {/* 收藏的快速入口 */}
        {!sidebarCollapsed && (
          <div className="space-y-1">
            <NavLink
              to="/profile/office_alice"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <div className="h-5 w-5 rounded-full bg-blue-100" />
              Alice（分析师）
            </NavLink>
            <NavLink
              to="/profile/office_bob"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <div className="h-5 w-5 rounded-full bg-purple-100" />
              Bob（开发工程师）
            </NavLink>
          </div>
        )}
      </nav>

      {/* 底部导航 */}
      <div className="space-y-1 border-t p-3">
        {bottomNavItems.map((item) => (
          <NavItemRenderer key={item.path} item={item} collapsed={sidebarCollapsed} />
        ))}
      </div>

      {/* 折叠按钮 */}
      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border bg-card text-muted-foreground shadow-sm hover:text-foreground"
      >
        {sidebarCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
      </button>
    </aside>
  );
}
