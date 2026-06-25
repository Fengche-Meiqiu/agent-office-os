import { Badge } from '@/components/ui/badge';
import type { Platform } from '@/types';

interface PlatformBadgeProps {
  platform: Platform;
  className?: string;
}

const platformColors: Record<Platform, string> = {
  Hermes: 'bg-blue-100 text-blue-700 hover:bg-blue-100',
  OpenClaw: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100',
  CrewAI: 'bg-purple-100 text-purple-700 hover:bg-purple-100',
  LangGraph: 'bg-orange-100 text-orange-700 hover:bg-orange-100',
};

export function PlatformBadge({ platform, className }: PlatformBadgeProps) {
  return (
    <Badge className={`${platformColors[platform]} ${className || ''}`}>
      {platform}
    </Badge>
  );
}
