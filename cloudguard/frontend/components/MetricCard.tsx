import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'rose' | 'amber' | 'cyan' | 'emerald';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
}) => {
  const variantStyles = {
    default: 'border-slate-800 bg-slate-900/60 text-slate-300',
    rose: 'border-rose-900/40 bg-rose-950/20 text-rose-400',
    amber: 'border-amber-900/40 bg-amber-950/20 text-amber-400',
    cyan: 'border-cyan-900/40 bg-cyan-950/20 text-cyan-400',
    emerald: 'border-emerald-900/40 bg-emerald-950/20 text-emerald-400',
  };

  const iconStyles = {
    default: 'bg-slate-800 text-slate-300',
    rose: 'bg-rose-500/20 text-rose-400',
    amber: 'bg-amber-500/20 text-amber-400',
    cyan: 'bg-cyan-500/20 text-cyan-400',
    emerald: 'bg-emerald-500/20 text-emerald-400',
  };

  return (
    <div className={`p-4 rounded-xl border ${variantStyles[variant]} backdrop-blur transition hover:border-slate-700`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-lg ${iconStyles[variant]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold font-mono text-slate-100">{value}</span>
      </div>

      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
};
