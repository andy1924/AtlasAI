'use client';

import React, { useEffect, useState } from 'react';
import { ShieldAlert, Activity, RefreshCw, Server, AlertTriangle } from 'lucide-react';
import { fetchHealth, HealthResponse } from '@/lib/api';

export const Navbar = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastCheck, setLastCheck] = useState<string>('');

  const checkHealth = async () => {
    setLoading(true);
    try {
      const data = await fetchHealth();
      setHealth(data);
      setLastCheck(new Date().toLocaleTimeString());
    } catch {
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold tracking-wider text-slate-100 text-lg">CLOUDGUARD</h1>
            <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono">v1.0-SOC</span>
          </div>
          <p className="text-xs text-slate-400">AI-Assisted Runtime Threat Detection & Response</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Backend & DB Health Indicator */}
        <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-slate-300 font-mono text-xs">
              API: {health ? health.status.toUpperCase() : 'OFFLINE'}
            </span>
          </div>

          <div className="h-3 w-px bg-slate-800" />

          <div className="flex items-center gap-1.5 text-slate-400">
            <Server className="w-3.5 h-3.5" />
            <span className="font-mono text-[11px]">DB: {health?.database || 'disconnected'}</span>
          </div>

          <button
            onClick={checkHealth}
            disabled={loading}
            className="ml-1 text-slate-400 hover:text-slate-200 transition"
            title="Refresh status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Live Lab Indicator */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-indigo-300 text-xs font-mono">
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          <span>LAB MODE: SIMULATED TELEMETRY</span>
        </div>
      </div>
    </header>
  );
};
