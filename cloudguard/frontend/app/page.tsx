'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MetricCard } from '@/components/MetricCard';
import { ThreatFeed } from '@/components/ThreatFeed';
import { RiskBadge } from '@/components/Badges';
import { fetchAnalytics, fetchThreats, runAllSimulations, AnalyticsSummary } from '@/lib/api';
import { ShieldAlert, AlertTriangle, Box, Activity, Zap, Play, ArrowRight } from 'lucide-react';

export default function OverviewPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [threats, setThreats] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  const loadData = async () => {
    try {
      const [anData, thData] = await Promise.all([fetchAnalytics(), fetchThreats()]);
      setAnalytics(anData);
      setThreats(thData);
    } catch (e) {
      console.error('Failed to fetch dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleQuickDemo = async () => {
    setSimulating(true);
    try {
      await runAllSimulations();
      await loadData();
    } catch (e) {
      console.error('Demo error:', e);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            SOC Operations Center
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
              SYSTEM ONLINE
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-Time Runtime Monitoring • Behavioral Anomaly Engine • Automated Containment
          </p>
        </div>

        <button
          onClick={handleQuickDemo}
          disabled={simulating}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-semibold text-sm hover:bg-amber-400 transition disabled:opacity-50 shadow-lg shadow-amber-500/20"
        >
          <Play className={`w-4 h-4 fill-current ${simulating ? 'animate-spin' : ''}`} />
          {simulating ? 'Running Attack Simulation...' : 'Trigger Attack Simulation'}
        </button>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Monitored Containers"
          value={analytics?.total_containers ?? 0}
          subtitle={`${analytics?.active_containers ?? 0} active in lab`}
          icon={Box}
          variant="cyan"
        />
        <MetricCard
          title="Open Incidents"
          value={analytics?.open_incidents ?? 0}
          subtitle={`${analytics?.critical_incidents ?? 0} CRITICAL priority`}
          icon={ShieldAlert}
          variant="rose"
        />
        <MetricCard
          title="Threats Detected Today"
          value={analytics?.threats_today ?? 0}
          subtitle={`Avg risk score: ${analytics?.avg_risk_score ?? 0}/100`}
          icon={AlertTriangle}
          variant="amber"
        />
        <MetricCard
          title="Total Events Processed"
          value={analytics?.total_events ?? 0}
          subtitle={`Detection rate: ${((analytics?.detection_rate ?? 0) * 100).toFixed(2)}%`}
          icon={Activity}
          variant="emerald"
        />
      </div>

      {/* Main Grid: Live Feed & Container Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Threat Stream (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <ThreatFeed threats={threats} loading={loading} />
        </div>

        {/* Sidebar Summary (1 col) */}
        <div className="space-y-6">
          {/* Quick Demo Launch Card */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 text-sm font-semibold">
              <Zap className="w-4 h-4" />
              <span>Academic Demo Scenarios</span>
            </div>
            <p className="text-xs text-slate-400">
              Instantly generate realistic runtime events to demonstrate threat detection, risk scoring, and response.
            </p>
            <div className="space-y-2 pt-1">
              <Link
                href="/demo"
                className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs font-medium transition"
              >
                <span>Launch Attack Simulator</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Quick Stats: Incidents by Severity */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
            <h3 className="text-sm font-semibold text-slate-200">Severity Breakdown</h3>

            <div className="space-y-2">
              {[
                { label: 'CRITICAL', count: analytics?.incidents_by_severity?.CRITICAL ?? 0, color: 'bg-rose-500' },
                { label: 'HIGH', count: analytics?.incidents_by_severity?.HIGH ?? 0, color: 'bg-orange-500' },
                { label: 'MEDIUM', count: analytics?.incidents_by_severity?.MEDIUM ?? 0, color: 'bg-amber-500' },
                { label: 'LOW', count: analytics?.incidents_by_severity?.LOW ?? 0, color: 'bg-emerald-500' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${item.color}`} />
                    <span className="text-slate-400">{item.label}</span>
                  </div>
                  <span className="text-slate-200 font-bold">{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
