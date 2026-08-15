import React from 'react';

interface SeverityBadgeProps {
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  const sev = severity.toUpperCase();
  let styles = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';

  if (sev === 'CRITICAL') {
    styles = 'bg-rose-500/15 text-rose-400 border-rose-500/40 animate-pulse';
  } else if (sev === 'HIGH') {
    styles = 'bg-orange-500/15 text-orange-400 border-orange-500/40';
  } else if (sev === 'MEDIUM') {
    styles = 'bg-amber-500/15 text-amber-400 border-amber-500/30';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {sev}
    </span>
  );
};

interface StatusBadgeProps {
  status: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const st = status.toUpperCase();
  let styles = 'bg-slate-800 text-slate-400 border-slate-700';

  if (st === 'OPEN') {
    styles = 'bg-rose-950/60 text-rose-300 border-rose-800/60';
  } else if (st === 'INVESTIGATING') {
    styles = 'bg-amber-950/60 text-amber-300 border-amber-800/60';
  } else if (st === 'CONTAINED') {
    styles = 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60';
  } else if (st === 'RESOLVED') {
    styles = 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60';
  } else if (st === 'FALSE_POSITIVE') {
    styles = 'bg-purple-950/60 text-purple-300 border-purple-800/60';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border ${styles}`}>
      {st.replace('_', ' ')}
    </span>
  );
};

interface RiskBadgeProps {
  score: number;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score }) => {
  let color = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  if (score > 75) color = 'text-rose-400 bg-rose-500/10 border-rose-500/30 font-bold';
  else if (score > 50) color = 'text-orange-400 bg-orange-500/10 border-orange-500/30';
  else if (score > 25) color = 'text-amber-400 bg-amber-500/10 border-amber-500/30';

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono border ${color}`}>
      Risk: {score.toFixed(0)}/100
    </span>
  );
};
