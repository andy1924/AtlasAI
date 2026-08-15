'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchIncidents, Incident } from '@/lib/api';
import { SeverityBadge, StatusBadge, RiskBadge } from '@/components/Badges';
import { AlertOctagon, Filter, ChevronRight, Search } from 'lucide-react';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const data = await fetchIncidents({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      });
      setIncidents(data);
    } catch (e) {
      console.error('Failed to load incidents:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [statusFilter, severityFilter]);

  const filteredIncidents = incidents.filter((inc) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      inc.title.toLowerCase().includes(term) ||
      (inc.container_name && inc.container_name.toLowerCase().includes(term)) ||
      (inc.detection_rule && inc.detection_rule.toLowerCase().includes(term)) ||
      `inc-${inc.incident_number}`.includes(term)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-400" />
            Security Incidents
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Correlated runtime threat incidents and automated response status
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search incidents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">OPEN</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="FALSE_POSITIVE">FALSE POSITIVE</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="border border-slate-800 rounded-xl bg-slate-900/60 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <div className="inline-block w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-2" />
            Loading security incidents...
          </div>
        ) : filteredIncidents.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No security incidents match the selected filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase text-[10px] font-mono">
                <tr>
                  <th className="p-3.5">ID</th>
                  <th className="p-3.5">Severity</th>
                  <th className="p-3.5">Threat / Title</th>
                  <th className="p-3.5">Target</th>
                  <th className="p-3.5">MITRE ATT&CK</th>
                  <th className="p-3.5">Risk</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Time</th>
                  <th className="p-3.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredIncidents.map((inc) => (
                  <tr key={inc.id} className="hover:bg-slate-800/40 transition group">
                    <td className="p-3.5 font-bold text-slate-400">INC-{inc.incident_number}</td>
                    <td className="p-3.5">
                      <SeverityBadge severity={inc.severity} />
                    </td>
                    <td className="p-3.5">
                      <Link
                        href={`/incidents/${inc.id}`}
                        className="font-sans font-medium text-slate-100 group-hover:text-cyan-400 transition"
                      >
                        {inc.title}
                      </Link>
                      {inc.detection_rule && (
                        <div className="text-[10px] text-slate-500 mt-0.5">{inc.detection_rule}</div>
                      )}
                    </td>
                    <td className="p-3.5 text-slate-300">{inc.container_name || inc.container_id || 'Host'}</td>
                    <td className="p-3.5">
                      {inc.mitre_technique_id ? (
                        <span className="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/60 text-indigo-300 text-[10px]">
                          {inc.mitre_technique_id}
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="p-3.5">
                      <RiskBadge score={inc.risk_score} />
                    </td>
                    <td className="p-3.5">
                      <StatusBadge status={inc.status} />
                    </td>
                    <td className="p-3.5 text-slate-400">{new Date(inc.created_at).toLocaleTimeString()}</td>
                    <td className="p-3.5">
                      <Link href={`/incidents/${inc.id}`} className="text-slate-500 group-hover:text-cyan-400 transition">
                        <ChevronRight className="w-4 h-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
