import { Avatar } from '@/components/ui/avatar';
import { StatusBadge } from './StatusBadge';
import { cn } from '@/lib/utils';
import type { AgentStatus } from '@/types';

interface AgentAvatarProps {
  src?: string;
  name: string;
  status?: AgentStatus | 'ONLINE' | 'OFFLINE' | 'BUSY';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showStatus?: boolean;
  className?: string;
}

export function AgentAvatar({
  src,
  name,
  status = 'ONLINE',
  size = 'md',
  showStatus = true,
  className,
}: AgentAvatarProps) {
  return (
    <div className={cn('relative inline-block', className)}>
      <Avatar src={src} fallback={name} size={size} />
      {showStatus && (
        <div className="absolute -bottom-0.5 -right-0.5">
          <StatusBadge status={status} showLabel={false} size="sm" />
        </div>
      )}
    </div>
  );
}
