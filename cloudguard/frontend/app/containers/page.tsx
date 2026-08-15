'use client';

import React, { useEffect, useState } from 'react';
import { fetchContainers, Container } from '@/lib/api';
import { RiskBadge } from '@/components/Badges';
import { Box, Cpu, HardDrive, ShieldCheck, Server, AlertCircle } from 'lucide-react';

export default function ContainersPage() {
  const [containers, setContainers] = useState<Container[]>([]);
  const [loading, setLoading] = useState(true);

  const loadContainers = async () => {
    try {
      const data = await fetchContainers();
      setContainers(data);
    } catch (e) {
      console.error('Failed to load containers:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContainers();
    const interval = setInterval(loadContainers, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Box className="w-5 h-5 text-cyan-400" />
          Container Monitoring
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Runtime observability of monitored container instances and risk scores
        </p>
      </div>

      {/* Containers Grid */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-sm">
          <div className="inline-block w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-2" />
          Loading tracked containers...
        </div>
      ) : containers.length === 0 ? (
        <div className="p-12 text-center border border-slate-800 rounded-xl bg-slate-900/40 text-slate-400 text-sm space-y-2">
          <Server className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="font-medium text-slate-200">No Containers Registered</p>
          <p className="text-xs text-slate-500">Run a simulation from the Attack Simulator to auto-register containers.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {containers.map((c) => (
            <div key={c.id} className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur space-y-4 hover:border-slate-700 transition">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                    <h3 className="font-bold text-slate-100 text-sm font-mono">{c.name}</h3>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono block mt-0.5">{c.container_id}</span>
                </div>
                <RiskBadge score={c.risk_score} />
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between text-slate-400">
                  <span>Image:</span>
                  <span className="text-slate-200 font-semibold">{c.image}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Host:</span>
                  <span className="text-slate-200">{c.host}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Threats Logged:</span>
                  <span className={c.threat_count > 0 ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                    {c.threat_count}
                  </span>
                </div>
              </div>

              {/* Resource Usage Bars */}
              <div className="pt-3 border-t border-slate-800 space-y-2 text-xs">
                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1 font-mono">
                    <span className="flex items-center gap-1"><Cpu className="w-3 h-3 text-cyan-400" /> CPU Usage</span>
                    <span>{c.cpu_percent}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full transition-all ${c.cpu_percent > 80 ? 'bg-rose-500' : 'bg-cyan-400'}`}
                      style={{ width: `${Math.min(c.cpu_percent, 100)}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1 font-mono">
                    <span className="flex items-center gap-1"><HardDrive className="w-3 h-3 text-indigo-400" /> Memory</span>
                    <span>{c.memory_percent}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-indigo-400 transition-all"
                      style={{ width: `${Math.min(c.memory_percent, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
