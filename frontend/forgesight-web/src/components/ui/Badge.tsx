import React from 'react';

interface BadgeProps {
  label: string;
  colorClass: string; // e.g. 'bg-status-open text-white'
}

/** Color is always paired with visible text — never the sole status signal. */
export function Badge({ label, colorClass }: BadgeProps) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${colorClass}`}>
      {label}
    </span>
  );
}