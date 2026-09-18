import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { IncidentStatus } from '@/types/incidents';

const STATUS_CONFIG: Record<IncidentStatus, { label: string; colorClass: string }> = {
  open: { label: 'Open', colorClass: 'bg-slate-500 text-white' },
  in_progress: { label: 'In Progress', colorClass: 'bg-blue-600 text-white' },
  awaiting_approval: { label: 'Awaiting Approval', colorClass: 'bg-amber-600 text-white' },
  closed: { label: 'Closed', colorClass: 'bg-green-600 text-white' },
  escalated: { label: 'Escalated', colorClass: 'bg-red-600 text-white' },
};

export function IncidentStatusBadge({ status }: { status: IncidentStatus }) {
  const config = STATUS_CONFIG[status];
  return <Badge label={config.label} colorClass={config.colorClass} />;
}