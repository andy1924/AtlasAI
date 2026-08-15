'use client';

import React, { useEffect, useState } from 'react';
import { fetchAnalytics, AnalyticsSummary } from '@/lib/api';
import { BarChart3, PieChart, TrendingUp, ShieldAlert } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart as RePieChart,
  Pie,
  Cell,
} from 'recharts';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics()
      .then(setAnalytics)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400 text-sm">
        <div className="inline-block w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-2" />
        Loading SOC analytics...
      </div>
    );
  }

  const eventsData = Object.entries(analytics?.events_by_type || {}).map(([type, count]) => ({
    name: type,
    count,
  }));

  const severityData = Object.entries(analytics?.incidents_by_severity || {}).map(([sev, count]) => ({
    name: sev,
    count,
  }));

  const SEVERITY_COLORS: Record<string, string> = {
    CRITICAL: '#f43f5e',
    HIGH: '#f97316',
    MEDIUM: '#f59e0b',
    LOW: '#10b981',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-400" />
          Threat Analytics & Benchmark Metrics
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Quantitative pipeline metrics: detection rate, event breakdown, and severity distributions
        </p>
      </div>

      {/* Metrics Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 font-mono">
          <span className="text-xs text-slate-400 uppercase">Detection Pipeline Rate</span>
          <div className="text-2xl font-bold text-cyan-400 mt-1">
            {((analytics?.detection_rate ?? 0) * 100).toFixed(2)}%
          </div>
          <span className="text-[11px] text-slate-500">Incidents generated per event</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 font-mono">
          <span className="text-xs text-slate-400 uppercase">Average Incident Risk</span>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {analytics?.avg_risk_score ?? 0} / 100
          </div>
          <span className="text-[11px] text-slate-500">Mean risk across all open threats</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 font-mono">
          <span className="text-xs text-slate-400 uppercase">Total Runtime Events</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {analytics?.total_events ?? 0}
          </div>
          <span className="text-[11px] text-slate-500">Normalized telemetry events</span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Events by Type Bar Chart */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200">Runtime Telemetry Events by Type</h3>
          {eventsData.length === 0 ? (
            <p className="text-xs text-slate-500 font-mono py-12 text-center">No telemetry events logged yet.</p>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={eventsData}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Severity Distribution Pie Chart */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200">Incidents by Severity</h3>
          {severityData.length === 0 ? (
            <p className="text-xs text-slate-500 font-mono py-12 text-center">No security incidents logged yet.</p>
          ) : (
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <RePieChart>
                  <Pie
                    data={severityData}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name] || '#94a3b8'} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                </RePieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
