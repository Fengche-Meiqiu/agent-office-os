import { cn } from '@/lib/utils';
import type { AgentStatus } from '@/types';

interface StatusBadgeProps {
  status: AgentStatus | 'ONLINE' | 'OFFLINE' | 'BUSY';
  showLabel?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  ONLINE: { label: '在线', color: 'text-status-online', bg: 'bg-status-online' },
  WORKING: { label: '忙碌中', color: 'text-status-working', bg: 'bg-status-working' },
  MEETING: { label: '会议中', color: 'text-status-meeting', bg: 'bg-status-meeting' },
  OFFLINE: { label: '离线', color: 'text-status-offline', bg: 'bg-status-offline' },
  ERROR: { label: '异常', color: 'text-status-error', bg: 'bg-status-error' },
  BUSY: { label: '忙碌', color: 'text-status-working', bg: 'bg-status-working' },
};

export function StatusBadge({ status, showLabel = true, size = 'md', className }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.OFFLINE;
  const dotSize = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2';
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <div className={cn('inline-flex items-center gap-1.5', className)}>
      <span className={cn('rounded-full', dotSize, config.bg, status === 'ONLINE' && 'animate-pulseGlow')} />
      {showLabel && <span className={cn(textSize, 'font-medium', config.color)}>{config.label}</span>}
    </div>
  );
}
