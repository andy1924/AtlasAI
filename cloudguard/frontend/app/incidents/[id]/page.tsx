'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { fetchIncidentById, acknowledgeIncident, resolveIncident, Incident } from '@/lib/api';
import { SeverityBadge, StatusBadge, RiskBadge } from '@/components/Badges';
import { ArrowLeft, ShieldAlert, CheckCircle, Clock, FileText, Server, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function IncidentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'evidence'>('overview');

  const loadData = async () => {
    try {
      const data = await fetchIncidentById(resolvedParams.id);
      setIncident(data);
    } catch (e) {
      console.error('Failed to load incident detail:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [resolvedParams.id]);

  const handleAcknowledge = async () => {
    setActionLoading(true);
    try {
      await acknowledgeIncident(resolvedParams.id);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async () => {
    setActionLoading(true);
    try {
      await resolveIncident(resolvedParams.id);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400 text-sm">
        <div className="inline-block w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-2" />
        Loading incident investigation details...
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="p-12 text-center text-slate-400 text-sm space-y-4">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
        <p>Incident not found.</p>
        <Link href="/incidents" className="text-cyan-400 text-xs hover:underline">
          Back to Incidents
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link href="/incidents" className="inline-flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition font-mono">
        <ArrowLeft className="w-4 h-4" />
        Back to Incidents
      </Link>

      {/* Incident Header */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono font-bold text-slate-400">INC-{incident.incident_number}</span>
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <RiskBadge score={incident.risk_score} />
            </div>

            <h1 className="text-2xl font-bold text-slate-100">{incident.title}</h1>
            <p className="text-xs text-slate-400">{incident.description}</p>
          </div>

          {/* Response Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            {incident.status === 'OPEN' && (
              <button
                onClick={handleAcknowledge}
                disabled={actionLoading}
                className="px-3.5 py-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 font-semibold text-xs hover:bg-amber-500/20 transition disabled:opacity-50"
              >
                Acknowledge
              </button>
            )}

            {incident.status !== 'RESOLVED' && (
              <button
                onClick={handleResolve}
                disabled={actionLoading}
                className="px-3.5 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold text-xs hover:bg-emerald-500/20 transition disabled:opacity-50 flex items-center gap-1.5"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                Resolve Incident
              </button>
            )}
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-3 border-t border-slate-800/80 text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[10px]">Target Container</span>
            <span className="text-slate-200 font-bold">{incident.container_name || incident.container_id || 'Host'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">Detection Rule</span>
            <span className="text-slate-200">{incident.detection_rule || 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">MITRE ATT&CK</span>
            <span className="text-indigo-400 font-bold">{incident.mitre_technique_id ? `${incident.mitre_technique_id}: ${incident.mitre_technique}` : 'None'}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px]">First Seen</span>
            <span className="text-slate-200">{new Date(incident.first_seen).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 text-xs font-medium">
        {[
          { id: 'overview', label: 'Risk & Indicators' },
          { id: 'timeline', label: 'Attack Timeline' },
          { id: 'evidence', label: 'Raw Evidence' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2.5 border-b-2 transition ${
              activeTab === tab.id
                ? 'border-cyan-400 text-cyan-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Overview & Risk Breakdown */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Risk Factors Breakdown */}
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              Transparent Risk Factor Breakdown
            </h3>

            {incident.risk_factors?.factors ? (
              <div className="space-y-3">
                {incident.risk_factors.factors.map((factor, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs">
                    <div className="flex items-center justify-between font-mono">
                      <span className="font-bold text-slate-200">{factor.name}</span>
                      <span className="text-amber-400 font-bold">+{factor.contribution} pts</span>
                    </div>
                    <p className="text-slate-400 text-[11px] mt-1">{factor.reason}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 font-mono">No detailed risk factor tree available.</p>
            )}
          </div>

          {/* Attack Indicators & Recommendations */}
          <div className="space-y-6">
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
              <h3 className="text-sm font-semibold text-slate-200">Observed Attack Indicators</h3>
              <ul className="space-y-2 text-xs font-mono">
                {incident.attack_indicators?.map((ind, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-rose-300">
                    <span className="text-rose-500">•</span>
                    <span>{ind}</span>
                  </li>
                )) || <li className="text-slate-500">None</li>}
              </ul>
            </div>

            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
              <h3 className="text-sm font-semibold text-slate-200">Recommended Analyst Actions</h3>
              <ul className="space-y-2 text-xs text-slate-300">
                {incident.recommended_actions?.map((act, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{act}</span>
                  </li>
                )) || <li className="text-slate-500">None</li>}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Visual Attack Timeline */}
      {activeTab === 'timeline' && (
        <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/60 space-y-6">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            Correlated Event Timeline
          </h3>

          <div className="relative pl-6 space-y-6 border-l-2 border-slate-800">
            <div className="relative group">
              <span className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-slate-700 border-2 border-slate-950" />
              <div className="text-xs font-mono text-slate-400">{new Date(incident.first_seen).toLocaleTimeString()}</div>
              <div className="text-sm font-medium text-slate-200">Normal Runtime Telemetry Recorded</div>
              <div className="text-xs text-slate-400">Baseline container activity initialized on host {incident.host || 'node-01'}</div>
            </div>

            <div className="relative group">
              <span className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-amber-500 border-2 border-slate-950 animate-ping" />
              <span className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-amber-500 border-2 border-slate-950" />
              <div className="text-xs font-mono text-amber-400">{new Date(incident.created_at).toLocaleTimeString()}</div>
              <div className="text-sm font-bold text-rose-300">Detection Triggered: {incident.title}</div>
              <div className="text-xs text-slate-300 mt-1 p-2 rounded bg-slate-950 border border-slate-800">
                Rule {incident.detection_rule} matched event pattern. Assigned risk score {incident.risk_score}/100 ({incident.severity}).
              </div>
            </div>

            {incident.status === 'RESOLVED' && (
              <div className="relative group">
                <span className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-slate-950" />
                <div className="text-xs font-mono text-emerald-400">Incident Resolved</div>
                <div className="text-sm font-medium text-emerald-300">Containment & Analyst Verification Complete</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Raw Evidence JSON */}
      {activeTab === 'evidence' && (
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-950 font-mono text-xs text-emerald-400 overflow-x-auto">
          <pre>{JSON.stringify(incident.evidence || incident, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
