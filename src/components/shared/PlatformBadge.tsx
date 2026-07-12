import { Badge } from '@/components/ui/badge';
import type { Platform } from '@/types';

interface PlatformBadgeProps {
  platform: Platform;
  className?: string;
}

const platformColors: Record<Platform, string> = {
  Hermes: 'bg-blue-100 text-blue-700 hover:bg-blue-100',
};

export function PlatformBadge({ platform, className }: PlatformBadgeProps) {
  return (
    <Badge className={`${platformColors[platform]} ${className || ''}`}>
      {platform}
    </Badge>
  );
}

