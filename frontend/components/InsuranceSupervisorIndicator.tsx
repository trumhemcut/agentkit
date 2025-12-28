import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Shield, FileText, ClipboardList, DollarSign, Headphones } from 'lucide-react';

interface InsuranceSupervisorIndicatorProps {
  specialist?: string;
  isActive?: boolean;
}

const specialistConfig: Record<string, {
  name: string;
  nameVi: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}> = {
  policy: {
    name: 'Policy Expert',
    nameVi: 'Chuyên gia Chính sách',
    icon: FileText,
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  },
  claims: {
    name: 'Claims Expert',
    nameVi: 'Chuyên gia Bồi thường',
    icon: ClipboardList,
    color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
  },
  quoting: {
    name: 'Quoting Expert',
    nameVi: 'Chuyên gia Báo giá',
    icon: DollarSign,
    color: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
  },
  support: {
    name: 'Customer Support',
    nameVi: 'Hỗ trợ Khách hàng',
    icon: Headphones,
    color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
  }
};

/**
 * Insurance Supervisor Indicator Component
 * 
 * Displays the current specialist handling the insurance query.
 * Shows supervisor badge when no specialist is selected,
 * or specialist badge with routing arrow when specialist is active.
 */
export function InsuranceSupervisorIndicator({ 
  specialist, 
  isActive = false 
}: InsuranceSupervisorIndicatorProps) {
  if (!specialist) {
    return (
      <Badge variant="outline" className="gap-1">
        <Shield className="h-3 w-3" />
        Insurance Supervisor
      </Badge>
    );
  }

  const config = specialistConfig[specialist];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className="gap-1">
        <Shield className="h-3 w-3" />
        Supervisor
      </Badge>
      <span className="text-xs text-muted-foreground">→</span>
      <Badge className={`gap-1 ${config.color}`}>
        <Icon className="h-3 w-3" />
        {config.nameVi}
      </Badge>
      {isActive && (
        <span 
          className="inline-flex h-2 w-2 rounded-full bg-green-500 animate-pulse" 
          role="status"
          aria-label="Active indicator"
        />
      )}
    </div>
  );
}
