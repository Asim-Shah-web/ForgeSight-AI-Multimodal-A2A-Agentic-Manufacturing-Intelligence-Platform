import React from 'react';
import { IncidentStatus } from '@/types/incidents';

interface IncidentFilterBarProps {
  status: IncidentStatus | '';
  lineId: string;
  onStatusChange: (status: IncidentStatus | '') => void;
  onLineIdChange: (lineId: string) => void;
}

const STATUSES: IncidentStatus[] = ['open', 'in_progress', 'awaiting_approval', 'closed', 'escalated'];

export function IncidentFilterBar({ status, lineId, onStatusChange, onLineIdChange }: IncidentFilterBarProps) {
  return (
    <div className="mb-4 flex gap-3">
      <select
        aria-label="Filter by status"
        className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        value={status}
        onChange={(e) => onStatusChange(e.target.value as IncidentStatus | '')}
      >
        <option value="">All statuses</option>
        {STATUSES.map((s) => (
          <option key={s} value={s}>
            {s.replace(/_/g, ' ')}
          </option>
        ))}
      </select>
      <input
        aria-label="Filter by line"
        placeholder="Line ID (e.g. SMT-LINE-03)"
        className="rounded-md border border-slate-300 px-3 py-2 text-sm"
        value={lineId}
        onChange={(e) => onLineIdChange(e.target.value)}
      />
    </div>
  );
}