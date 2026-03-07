"use client";

import { useState, useEffect } from "react";

// ==========================================
// TYPESCRIPT INTERFACES
// ==========================================

interface Shipment {
  shipment_id: string;
  origin: string;
  destination: string;
  carrier: string;
  weight_kg: number;
  distance_km: number;
  eta_hours: number;
  status: string;
  delay_probability: number;
  operational_cost: number;
  partner_reliability: number;
  timestamp: string;
}

interface Alert {
  id: string;
  type: string;
  location: string;
  severity: string;
  description: string;
}

interface AgentLog {
  timestamp: string;
  hypothesis: string;
  decision: string;
  action_taken: string;
  confidence: number;
  action_type: string;
  severity_level: string;
  shipments_affected: number;
  autonomous: boolean;
}

interface ChaosScenario {
  type: string;
  location: string;
  severity: string;
  description: string;
}

interface NewsItem {
  title: string;
  source: string;
  url: string;
  chaos_type: string;
  location: string | null;
}

interface CarrierStat {
  carrier: string;
  total_shipments: number;
  delayed_shipments: number;
  reliability_score: number;
  status: string;
}

interface OutcomeResult {
  successful: number;
  failed: number;
  details: Array<{
    shipment_id: string;
    status: string;
    delay_probability: number;
    outcome: string;
  }>;
}

// ==========================================
// HELPER COMPONENTS
// ==========================================

function ConfidenceMeter({ confidence }: { confidence: number }) {
  const color =
    confidence >= 75 ? "bg-green-500" :
    confidence >= 50 ? "bg-yellow-500" :
    "bg-red-500";
  return (
    <div className="mt-2">
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>Agent Confidence</span>
        <span className={confidence >= 75 ? "text-green-400" : confidence >= 50 ? "text-yellow-400" : "text-red-400"}>
          {confidence}%
        </span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${confidence}%` }}
        />
      </div>
    </div>
  );
}

function ActionTypeBadge({ actionType }: { actionType: string }) {
  const styles: Record<string, string> = {
    REROUTE: "bg-blue-500/20 text-blue-400 border-blue-500/50",
    HOLD: "bg-orange-500/20 text-orange-400 border-orange-500/50",
    SWITCH_CARRIER: "bg-cyan-500/20 text-cyan-400 border-cyan-500/50",
    EXPEDITE: "bg-purple-500/20 text-purple-400 border-purple-500/50",
    ESCALATE: "bg-red-500/20 text-red-400 border-red-500/50",
    MONITOR: "bg-gray-500/20 text-gray-400 border-gray-500/50",
    HUMAN_APPROVED: "bg-green-500/20 text-green-400 border-green-500/50",
    EVALUATE: "bg-teal-500/20 text-teal-400 border-teal-500/50",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${styles[actionType] || "bg-gray-700 text-gray-400"}`}>
      {actionType}
    </span>
  );
}

// ==========================================
// MAIN DASHBOARD COMPONENT
// ==========================================

export default function Dashboard() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const [liveNews, setLiveNews] = useState<NewsItem[]>([]);
  const [carrierStats, setCarrierStats] = useState<CarrierStat[]>([]);
  const [outcomeResult, setOutcomeResult] = useState<OutcomeResult | null>(null);
  const [isAgentRunning, setIsAgentRunning] = useState<boolean>(false);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"logs" | "carriers" | "outcomes">("logs");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const itemsPerPage = 20;

  const chaosScenarios: ChaosScenario[] = [
    { type: "Port Bombing", location: "South Kathryntown", severity: "High", description: "Critical infrastructure destroyed. Total maritime halt." },
    { type: "Hurricane", location: "Haleview", severity: "High", description: "Category 5 hurricane halting all inbound and outbound traffic." },
    { type: "Traffic Jam", location: "Port Elizabeth", severity: "Low", description: "Severe congestion on main highway causing minor delays." },
    { type: "Piracy Threat", location: "North Sandraberg", severity: "Medium", description: "Vessels rerouting due to elevated security risks." },
    { type: "Port Strike", location: "Kellyland", severity: "Medium", description: "Port workers strike announced. Partial loading halt expected 48h." },
    { type: "Carrier Degradation", location: "Reedchester", severity: "Medium", description: "Logistics partner experiencing sudden operational degradation." },
  ];

  const fetchState = async () => {
    try {
      const [shipmentRes, alertRes, newsRes, carrierRes, historyRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/shipments"),
        fetch("http://127.0.0.1:8000/api/alerts"),
        fetch("http://127.0.0.1:8000/api/news"),
        fetch("http://127.0.0.1:8000/api/carrier-reliability"),
        fetch("http://127.0.0.1:8000/api/agent-history"),
      ]);
      const [shipmentData, alertData, newsData, carrierData, historyData] = await Promise.all([
        shipmentRes.json(), alertRes.json(), newsRes.json(),
        carrierRes.json(), historyRes.json()
      ]);

      setShipments(shipmentData.shipments || []);
      setAlerts(alertData.alerts || []);
      setLiveNews(newsData.news || []);
      setCarrierStats(carrierData.carrier_reliability || []);
      setAgentLogs(historyData.history || []);
    } catch (error) {
      console.error("Failed to fetch state:", error);
    }
  };

  useEffect(() => { fetchState(); }, []);

  const handleChaos = async (scenario: ChaosScenario) => {
    await fetch("http://127.0.0.1:8000/api/trigger-chaos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(scenario),
    });
    await handleRunAgent();
    setCurrentPage(1);
  };

  const handleRunAgent = async () => {
    setIsAgentRunning(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/run-agent", { method: "POST" });
      const data = await res.json();
      setShipments(data.updated_shipments);
      await fetchState();
    } catch (error) {
      console.error("Agent run failed:", error);
    }
    setIsAgentRunning(false);
  };

  const handleApprove = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/approve-actions", { method: "POST" });
      const data = await res.json();
      setShipments(data.updated_shipments);
      await fetchState();
    } catch (error) {
      console.error("Approval failed:", error);
    }
  };

  const handleEvaluateOutcomes = async () => {
    setIsEvaluating(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/evaluate-outcomes", { method: "POST" });
      const data = await res.json();
      setOutcomeResult(data.results);
      setActiveTab("outcomes");
      await fetchState();
    } catch (error) {
      console.error("Evaluation failed:", error);
    }
    setIsEvaluating(false);
  };

  const activeAlertLocations = alerts.map((a) => a.location);
  const pendingApprovals = shipments.filter((s) => s.status === "Pending Approval");

  const sortedShipments = [...shipments].sort((a, b) => {
    const priority: Record<string, number> = {
      "At Risk": 0, "Pending Approval": 1, "On Hold": 2,
      "Carrier Switch Pending": 3, "Expedited": 4,
      "Rerouted (Auto)": 5, "Rerouted (Approved)": 6,
    };
    return (priority[a.status] ?? 99) - (priority[b.status] ?? 99);
  });

  const totalPages = Math.ceil(sortedShipments.length / itemsPerPage);
  const currentShipments = sortedShipments.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const getStatusStyle = (status: string) => {
    const styles: Record<string, string> = {
      "At Risk": "bg-red-500/20 text-red-400 border border-red-500/50",
      "Pending Approval": "bg-yellow-500/20 text-yellow-400 border border-yellow-500/50",
      "Rerouted (Auto)": "bg-purple-500/20 text-purple-400",
      "Rerouted (Approved)": "bg-green-500/20 text-green-400",
      "On Hold": "bg-orange-500/20 text-orange-400",
      "Carrier Switch Pending": "bg-cyan-500/20 text-cyan-400",
      "Expedited": "bg-pink-500/20 text-pink-400",
      "Monitoring": "bg-gray-500/20 text-gray-400",
    };
    return styles[status] || "bg-blue-500/20 text-blue-400";
  };

  // Stats bar
  const atRiskCount = shipments.filter(s => s.status === "At Risk").length;
  const pendingCount = pendingApprovals.length;
  const resolvedCount = shipments.filter(s =>
    ["Rerouted (Auto)", "Rerouted (Approved)", "On Hold", "Expedited", "Carrier Switch Pending"].includes(s.status)
  ).length;
  const lastLog = agentLogs[0];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 font-sans">

      {/* ── HEADER ── */}
      <header className="flex justify-between items-center mb-6 border-b border-gray-700 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-blue-400">AtlasAI</h1>
          <p className="text-gray-400 text-sm">Autonomous Logistics Intelligence Layer</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Evaluate Outcomes button */}
          <button
            onClick={handleEvaluateOutcomes}
            disabled={isEvaluating}
            className="px-4 py-2 bg-teal-700 hover:bg-teal-600 disabled:opacity-50 text-white text-sm font-semibold rounded transition-colors"
          >
            {isEvaluating ? "Evaluating..." : "📊 Evaluate Outcomes"}
          </button>

          {/* Run Agent manually */}
          <button
            onClick={handleRunAgent}
            disabled={isAgentRunning}
            className="px-4 py-2 bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white text-sm font-semibold rounded transition-colors"
          >
            {isAgentRunning ? "[ PROCESSING... ]" : "▶ Run Agent"}
          </button>

          {/* Trigger chaos dropdown */}
          <div className="relative group z-50">
            <button className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded shadow-lg flex items-center gap-2">
              {isAgentRunning ? "[ PROCESSING ]" : "TRIGGER EVENT ▾"}
            </button>
            <div className="absolute right-0 mt-2 w-72 bg-gray-800 border border-red-900 rounded-md shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
              <div className="p-2 flex flex-col gap-1">
                {chaosScenarios.map((scenario, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleChaos(scenario)}
                    disabled={isAgentRunning}
                    className="text-left px-4 py-3 hover:bg-gray-700 rounded flex flex-col disabled:opacity-50"
                  >
                    <span className="font-bold text-sm text-red-400">{scenario.type}</span>
                    <span className="text-xs text-gray-400">@ {scenario.location} | {scenario.severity}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ── STATS BAR ── */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Total Tracked</p>
          <p className="text-2xl font-bold text-blue-400">{shipments.length}</p>
        </div>
        <div className={`bg-gray-800 rounded-lg p-4 border ${atRiskCount > 0 ? "border-red-700 animate-pulse" : "border-gray-700"}`}>
          <p className="text-xs text-gray-400 uppercase tracking-wide">At Risk</p>
          <p className={`text-2xl font-bold ${atRiskCount > 0 ? "text-red-400" : "text-gray-400"}`}>{atRiskCount}</p>
        </div>
        <div className={`bg-gray-800 rounded-lg p-4 border ${pendingCount > 0 ? "border-yellow-600" : "border-gray-700"}`}>
          <p className="text-xs text-gray-400 uppercase tracking-wide">Pending Approval</p>
          <p className={`text-2xl font-bold ${pendingCount > 0 ? "text-yellow-400" : "text-gray-400"}`}>{pendingCount}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Resolved</p>
          <p className="text-2xl font-bold text-green-400">{resolvedCount}</p>
        </div>
      </div>

      {/* ── HUMAN APPROVAL BANNER ── */}
      {pendingApprovals.length > 0 && (
        <div className="mb-6 p-6 bg-yellow-900/30 border border-yellow-600 rounded-lg shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-bold text-yellow-500">⚠️ [ACTION REQUIRED] Human Authorization</h2>
              <p className="text-yellow-200 text-sm mt-1">
                Agent halted autonomous execution. {pendingApprovals.length} shipment(s) require your approval.
              </p>
              {lastLog && (
                <p className="text-yellow-300 text-xs mt-2 font-mono">
                  Agent reasoning: {lastLog.hypothesis?.slice(0, 120)}...
                </p>
              )}
            </div>
            <button
              onClick={handleApprove}
              className="px-8 py-3 bg-yellow-600 hover:bg-yellow-500 text-black font-bold rounded shadow-lg transition-transform animate-pulse"
            >
              VERIFY & EXECUTE
            </button>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {pendingApprovals.map((s) => (
              <div key={s.shipment_id} className="bg-gray-900 p-2 rounded border border-yellow-700 text-xs whitespace-nowrap">
                <span className="text-yellow-400 font-mono">{s.shipment_id}</span>
                <span className="text-gray-400"> | {s.carrier} | risk: {(s.delay_probability * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── MAIN GRID ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* LEFT — Alerts + Shipments */}
        <div className="col-span-2 space-y-6">

          {/* Active Alerts */}
          <div className="bg-gray-800 p-5 rounded-lg border border-red-900/50">
            <h2 className="text-lg font-semibold mb-3 text-red-400">Active Disruption Alerts</h2>
            {alerts.length === 0 ? (
              <p className="text-gray-500 italic text-sm">No active disruptions detected.</p>
            ) : (
              <ul className="space-y-2">
                {alerts.map((a) => (
                  <li key={a.id} className="bg-red-900/20 border border-red-700/50 p-3 rounded flex justify-between items-center">
                    <div>
                      <strong className="text-red-400">{a.type}</strong>
                      <span className="text-gray-300"> @ {a.location}</span>
                      <span className="text-gray-400 text-sm"> — {a.description}</span>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-bold ml-3 shrink-0 ${
                      a.severity === "High" ? "bg-red-600" :
                      a.severity === "Medium" ? "bg-orange-500" :
                      "bg-yellow-500 text-black"
                    }`}>
                      {a.severity}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Shipment Table */}
          <div className="bg-gray-800 p-5 rounded-lg border border-gray-700">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-blue-300">Global Shipment Status</h2>
              <span className="text-sm text-gray-400">Tracking: {shipments.length}</span>
            </div>

            <div className="overflow-x-auto min-h-[400px]">
              <table className="w-full text-left text-sm">
                <thead className="text-gray-400 border-b border-gray-700">
                  <tr>
                    <th className="pb-2 pr-4">ID</th>
                    <th className="pb-2 pr-4">Route</th>
                    <th className="pb-2 pr-4">Carrier</th>
                    <th className="pb-2 pr-4">Delay Risk</th>
                    <th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {currentShipments.map((s) => {
                    const isAffected = activeAlertLocations.includes(s.origin) || activeAlertLocations.includes(s.destination);
                    return (
                      <tr key={s.shipment_id} className={`border-b border-gray-700/50 ${isAffected ? "bg-red-900/10" : ""}`}>
                        <td className="py-2 pr-4 font-mono text-xs">
                          {isAffected && <span className="text-red-500 mr-1">[!]</span>}
                          {s.shipment_id}
                        </td>
                        <td className="py-2 pr-4 text-xs">{s.origin} → {s.destination}</td>
                        <td className="py-2 pr-4 text-xs">{s.carrier}</td>
                        <td className="py-2 pr-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 bg-gray-700 rounded-full h-1.5">
                              <div
                                className={`h-1.5 rounded-full ${
                                  s.delay_probability > 0.6 ? "bg-red-500" :
                                  s.delay_probability > 0.3 ? "bg-yellow-500" : "bg-green-500"
                                }`}
                                style={{ width: `${s.delay_probability * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-400">{(s.delay_probability * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${getStatusStyle(s.status)}`}>
                            {s.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-700">
                <button
                  onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded text-sm"
                >
                  ← Previous
                </button>
                <span className="text-sm text-gray-400">Page {currentPage} of {totalPages}</span>
                <button
                  onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded text-sm"
                >
                  Next →
                </button>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="flex flex-col gap-6">

          {/* Tabbed Right Panel */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 flex flex-col" style={{ maxHeight: "60vh" }}>
            {/* Tab bar */}
            <div className="flex border-b border-gray-700">
              {(["logs", "carriers", "outcomes"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-3 text-xs font-semibold uppercase tracking-wide transition-colors ${
                    activeTab === tab
                      ? "text-blue-400 border-b-2 border-blue-400"
                      : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  {tab === "logs" ? "🤖 Agent Log" : tab === "carriers" ? "📦 Carriers" : "📊 Outcomes"}
                </button>
              ))}
            </div>

            <div className="overflow-y-auto p-4 flex-1">

              {/* Agent Logs Tab */}
              {activeTab === "logs" && (
                <div className="space-y-4">
                  {agentLogs.length === 0 ? (
                    <p className="text-gray-500 italic text-sm">Awaiting system events...</p>
                  ) : (
                    agentLogs.map((log, idx) => (
                      <div
                        key={idx}
                        className={`p-4 rounded border text-sm ${
                          log.action_type === "HUMAN_APPROVED" ? "bg-green-900/10 border-green-700/40" :
                          log.action_type === "ESCALATE" ? "bg-yellow-900/10 border-yellow-700/40" :
                          log.action_type === "EVALUATE" ? "bg-teal-900/10 border-teal-700/40" :
                          "bg-gray-900 border-gray-700"
                        }`}
                      >
                        <div className="flex justify-between items-center mb-2">
                          <ActionTypeBadge actionType={log.action_type} />
                          <span className="text-xs text-gray-500">
                            {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ""}
                          </span>
                        </div>

                        <div className="mb-2">
                          <span className="text-xs text-gray-500 uppercase tracking-wide block">Hypothesis</span>
                          <p className="text-gray-300 mt-1 text-xs leading-relaxed">{log.hypothesis}</p>
                        </div>

                        <div className="mb-2">
                          <span className="text-xs text-gray-500 uppercase tracking-wide block">Execution</span>
                          <p className={`font-semibold mt-1 text-xs ${
                            !log.autonomous ? "text-yellow-400" : "text-purple-400"
                          }`}>
                            {!log.autonomous ? "👤 [HUMAN] " : "🤖 [AUTO] "}
                            {log.action_taken}
                          </p>
                        </div>

                        <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                          <span>Affected: {log.shipments_affected} shipments</span>
                          <span>Severity: {log.severity_level}</span>
                        </div>

                        {log.confidence > 0 && log.action_type !== "EVALUATE" && (
                          <ConfidenceMeter confidence={log.confidence} />
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Carrier Reliability Tab */}
              {activeTab === "carriers" && (
                <div className="space-y-3">
                  <p className="text-xs text-gray-400 mb-3">Live reliability scores calculated from current delay probabilities.</p>
                  {carrierStats.length === 0 ? (
                    <p className="text-gray-500 italic text-sm">Loading carrier data...</p>
                  ) : (
                    carrierStats.map((c) => (
                      <div key={c.carrier} className="bg-gray-900 rounded p-3 border border-gray-700">
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-semibold text-sm">{c.carrier}</span>
                          <span className="text-xs">{c.status}</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 mb-1">
                          <div
                            className={`h-2 rounded-full ${
                              c.reliability_score >= 0.85 ? "bg-green-500" :
                              c.reliability_score >= 0.70 ? "bg-yellow-500" : "bg-red-500"
                            }`}
                            style={{ width: `${c.reliability_score * 100}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>{(c.reliability_score * 100).toFixed(1)}% reliable</span>
                          <span>{c.delayed_shipments}/{c.total_shipments} delayed</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Outcome Evaluation Tab */}
              {activeTab === "outcomes" && (
                <div>
                  {!outcomeResult ? (
                    <div className="text-center py-6">
                      <p className="text-gray-400 text-sm mb-3">Click "Evaluate Outcomes" to check if past agent actions worked.</p>
                      <p className="text-xs text-gray-500">This closes the LEARN loop — failures are recorded in ChromaDB so the agent improves over time.</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3 mb-4">
                        <div className="bg-green-900/20 rounded p-3 border border-green-700/40 text-center">
                          <p className="text-2xl font-bold text-green-400">{outcomeResult.successful}</p>
                          <p className="text-xs text-gray-400">Successful</p>
                        </div>
                        <div className="bg-red-900/20 rounded p-3 border border-red-700/40 text-center">
                          <p className="text-2xl font-bold text-red-400">{outcomeResult.failed}</p>
                          <p className="text-xs text-gray-400">Failed</p>
                        </div>
                      </div>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {outcomeResult.details.map((d, idx) => (
                          <div key={idx} className={`p-2 rounded border text-xs ${
                            d.outcome.includes("SUCCESS")
                              ? "bg-green-900/10 border-green-700/30"
                              : "bg-red-900/10 border-red-700/30"
                          }`}>
                            <div className="flex justify-between">
                              <span className="font-mono text-gray-300">{d.shipment_id}</span>
                              <span>{d.outcome.includes("SUCCESS") ? "✅" : "❌"}</span>
                            </div>
                            <div className="text-gray-400 mt-0.5">{d.status} — risk: {(d.delay_probability * 100).toFixed(0)}%</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Live News Radar */}
          <div className="bg-gray-800 p-5 rounded-lg border border-gray-700 overflow-y-auto" style={{ maxHeight: "35vh" }}>
            <h2 className="text-lg font-semibold mb-3 text-blue-300">🌍 Global Disruption Radar</h2>
            {liveNews.length === 0 ? (
              <p className="text-gray-500 italic text-sm">Scanning global OSINT feeds...</p>
            ) : (
              <div className="space-y-3">
                {liveNews.map((item, idx) => (
                  <div key={idx} className="p-3 rounded border border-gray-700 bg-gray-900 text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-red-400 font-bold">{item.chaos_type}</span>
                      {item.location && (
                        <span className="text-xs bg-red-900/30 text-red-300 px-1.5 py-0.5 rounded">
                          MATCH: {item.location}
                        </span>
                      )}
                    </div>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-200 hover:text-blue-400 transition-colors text-xs"
                    >
                      {item.title}
                    </a>
                    <p className="text-xs text-gray-500 mt-1">Source: {item.source}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}