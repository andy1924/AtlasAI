'use client';

import React from 'react';
import Link from 'next/link';
import { SeverityBadge, StatusBadge, RiskBadge } from './Badges';
import { Shield, ChevronRight, AlertCircle } from 'lucide-react';

interface ThreatItem {
  id: string;
  incident_number: number;
  title: string;
  severity: string;
  risk_score: number;
  status: string;
  container_name?: string;
  created_at: string;
}

interface ThreatFeedProps {
  threats: ThreatItem[];
  loading?: boolean;
}

export const ThreatFeed: React.FC<ThreatFeedProps> = ({ threats, loading }) => {
  if (loading) {
    return (
      <div className="p-8 text-center border border-slate-800 rounded-xl bg-slate-900/40 text-slate-400 text-sm">
        <div className="inline-block w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-2" />
        Loading real-time threat feed...
      </div>
    );
  }

  if (!threats || threats.length === 0) {
    return (
      <div className="p-8 text-center border border-slate-800 rounded-xl bg-slate-900/40 text-slate-400 text-sm space-y-2">
        <Shield className="w-8 h-8 text-emerald-400 mx-auto" />
        <p className="font-medium text-slate-200">No Threat Incidents Recorded Yet</p>
        <p className="text-xs text-slate-500">Run an attack scenario from the Simulator to trigger real pipeline events.</p>
      </div>
    );
  }

  return (
    <div className="border border-slate-800 rounded-xl bg-slate-900/60 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          <h3 className="text-sm font-semibold text-slate-200">Live Threat Stream</h3>
        </div>
        <span className="text-xs font-mono text-slate-400">{threats.length} events logged</span>
      </div>

      <div className="divide-y divide-slate-800/60 max-h-[420px] overflow-y-auto">
        {threats.map((threat) => (
          <Link
            key={threat.id}
            href={`/incidents/${threat.id}`}
            className="flex items-center justify-between p-3.5 hover:bg-slate-800/40 transition group"
          >
            <div className="flex items-center gap-3">
              <SeverityBadge severity={threat.severity} />

              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-slate-400">INC-{threat.incident_number}</span>
                  <span className="text-sm font-medium text-slate-200 group-hover:text-cyan-400 transition">
                    {threat.title}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                  <span>Target: <strong className="text-slate-300 font-mono">{threat.container_name || 'Host'}</strong></span>
                  <span>•</span>
                  <span>{new Date(threat.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <RiskBadge score={threat.risk_score} />
              <StatusBadge status={threat.status} />
              <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-300 transition" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};
