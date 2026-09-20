import React from 'react';
import { Card } from '@/components/ui/Card';

const DOMAIN_LABELS: Record<string, string> = {
  vision: 'Vision',
  telemetry: 'Telemetry',
  maintenance: 'Maintenance',
  component_lot: 'Component Lot',
  documents: 'Documents',
  historical: 'Historical Incidents',
};

export function EvidenceSummaryPanel({ summary }: { summary: Record<string, boolean> }) {
  const domains = Object.keys(DOMAIN_LABELS);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {domains.map((domain) => {
        const hasGap = summary[domain] === true;
        const hasData = domain in summary;
        return (
          <Card key={domain} className={hasGap ? 'border-amber-300' : hasData ? 'border-green-300' : ''}>
            <p className="text-sm font-medium">{DOMAIN_LABELS[domain]}</p>
            {!hasData && <p className="text-xs text-slate-400">Not yet gathered</p>}
            {hasData && hasGap && <p className="text-xs font-medium text-amber-700">No data available for this domain</p>}
            {hasData && !hasGap && <p className="text-xs font-medium text-green-700">Evidence gathered</p>}
          </Card>
        );
      })}
    </div>
  );
}