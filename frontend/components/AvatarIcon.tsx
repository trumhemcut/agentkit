import { User, Bot } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

interface AvatarIconProps {
  role: 'user' | 'agent';
  className?: string;
}

/**
 * Avatar Icon component
 * 
 * Displays user or agent avatar with appropriate icon
 */
export function AvatarIcon({ role, className }: AvatarIconProps) {
  return (
    <Avatar className={cn("h-8 w-8", className)}>
      <AvatarFallback className={cn(
        role === 'user' ? 'bg-blue-500' : 'bg-green-500',
        'text-white'
      )}>
        {role === 'user' ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </AvatarFallback>
    </Avatar>
  );
}
