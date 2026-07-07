import { NavLink } from 'react-router-dom';
import {
  BarChart3,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  LayoutGrid,
  MessageSquare,
  Settings,
  Store,
  Users,
  Wrench,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/appStore';

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

const mainNavItems: NavItem[] = [
  { label: 'Office', path: '/', icon: LayoutGrid },
  { label: 'Meeting Room', path: '/meeting', icon: Users },
  { label: 'Task Center', path: '/tasks', icon: CheckSquare },
  { label: 'Agent Marketplace', path: '/marketplace', icon: Store },
  { label: 'Chat Center', path: '/chat', icon: MessageSquare },
  { label: 'Outputs', path: '/outputs', icon: FolderOpen },
];

const bottomNavItems: NavItem[] = [
  { label: 'Tools', path: '/tools', icon: Wrench },
  { label: 'Dashboard', path: '/dashboard', icon: BarChart3 },
  { label: 'Settings', path: '/settings', icon: Settings },
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
          isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground'
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
      <div className="flex h-16 items-center gap-3 border-b px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-white">
          <LayoutGrid className="h-5 w-5" />
        </div>
        {!sidebarCollapsed && (
          <div className="flex flex-col">
            <span className="text-sm font-bold leading-tight">Agent Office</span>
            <span className="text-[10px] text-muted-foreground leading-tight">Hermes workspace</span>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-1 overflow-auto p-3">
        {mainNavItems.map((item) => (
          <NavItemRenderer key={item.path} item={item} collapsed={sidebarCollapsed} />
        ))}
      </nav>

      <div className="space-y-1 border-t p-3">
        {bottomNavItems.map((item) => (
          <NavItemRenderer key={item.path} item={item} collapsed={sidebarCollapsed} />
        ))}
      </div>

      <button
        onClick={toggleSidebar}
        className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border bg-card text-muted-foreground shadow-sm hover:text-foreground"
        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {sidebarCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
      </button>
    </aside>
  );
}
