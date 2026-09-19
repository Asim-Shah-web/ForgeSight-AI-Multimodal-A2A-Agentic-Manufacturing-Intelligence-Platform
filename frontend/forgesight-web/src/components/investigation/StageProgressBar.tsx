import React from 'react';

const STAGE_NAMES = [
  'Defect Detection & Threshold Trigger',
  'Incident Creation & Context Setup',
  'Visual Evidence Extraction',
  'Production & Telemetry Investigation',
  'Machine & Maintenance Check',
  'Component Lot & Supplier Correlation',
  'Technical SOP & Manual Retrieval',
  'Evidence Correlation & Synthesis',
  'Root-Cause Hypothesis Ranking',
  'Corrective Action Recommendation',
  'Human Engineer Review & Sign-Off',
  'Report Generation & Audit Trail',
];

export function StageProgressBar({ currentStage, completedStages }: { currentStage: number; completedStages: number[] }) {
  return (
    <ol className="space-y-1">
      {STAGE_NAMES.map((name, index) => {
        const stageNumber = index + 1;
        const isCompleted = completedStages.includes(stageNumber);
        const isCurrent = stageNumber === currentStage;
        return (
          <li key={stageNumber} className="flex items-center gap-2 text-sm">
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                isCompleted ? 'bg-green-600 text-white' : isCurrent ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-500'
              }`}
            >
              {stageNumber}
            </span>
            <span className={isCurrent ? 'font-semibold' : isCompleted ? 'text-slate-700' : 'text-slate-400'}>
              {name}
              {isCurrent && <span className="ml-2 text-xs font-normal text-blue-600">(current)</span>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}