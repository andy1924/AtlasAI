"use client";

import { useState, useEffect } from "react";

export default function Dashboard() {
  const [shipments, setShipments] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [isAgentRunning, setIsAgentRunning] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const chaosScenarios = [
    { type: "Port Bombing", location: "South Kathryntown", severity: "High", description: "Critical infrastructure destroyed. Total maritime halt." },
    { type: "Hurricane", location: "Haleview", severity: "High", description: "Category 5 hurricane halting all inbound and outbound traffic." },
    { type: "Traffic Jam", location: "Port Elizabeth", severity: "Low", description: "Severe congestion on main highway causing minor delays." },
    { type: "Piracy Threat", location: "North Sandraberg", severity: "Medium", description: "Vessels rerouting due to elevated security risks." }
  ];

  const fetchState = async () => {
    try {
      const [shipmentRes, alertRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/shipments"),
        fetch("http://127.0.0.1:8000/api/alerts"),
      ]);
      const shipmentData = await shipmentRes.json();
      const alertData = await alertRes.json();
      setShipments(shipmentData.shipments || []);
      setAlerts(alertData.alerts || []);
    } catch (error) {
      console.error("Failed to fetch state:", error);
    }
  };

  useEffect(() => {
    fetchState();
  }, []);

  const handleChaos = async (scenario: any) => {
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
      setAgentLogs((prev) => [data.log, ...prev]);
      setShipments(data.updated_shipments);
      fetchState();
    } catch (error) {
      console.error("Failed to run agent:", error);
    }
    setIsAgentRunning(false);
  };

  const handleApprove = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/approve-actions", { method: "POST" });
      const data = await res.json();
      setShipments(data.updated_shipments);

      setAgentLogs((prev) => [{
        hypothesis: "Human Operator Override",
        decision: "Reviewed and approved escalated AI mitigation plans.",
        action_taken: "Officially executed rerouting for high-risk shipments."
      }, ...prev]);

      fetchState();
    } catch (error) {
      console.error("Failed to approve actions:", error);
    }
  };

  const activeAlertLocations = alerts.map((a: any) => a.location);

  const pendingApprovals = shipments.filter((s: any) => s.status === "Pending Approval");

  const sortedShipments = [...shipments].sort((a: any, b: any) => {
    const aAffected = activeAlertLocations.includes(a.origin) || activeAlertLocations.includes(a.destination);
    const bAffected = activeAlertLocations.includes(b.origin) || activeAlertLocations.includes(b.destination);
    if (aAffected && !bAffected) return -1;
    if (!aAffected && bAffected) return 1;
    return 0;
  });

  const totalPages = Math.ceil(sortedShipments.length / itemsPerPage);
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentShipments = sortedShipments.slice(indexOfFirstItem, indexOfLastItem);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8 font-sans">
      <header className="flex justify-between items-center mb-8 border-b border-gray-700 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-blue-400">AtlasAI</h1>
          <p className="text-gray-400 text-sm">Autonomous Logistics Intelligence Layer</p>
        </div>

        <div className="flex gap-4">
          <div className="relative group z-50">
            <button className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded shadow-lg transition-transform active:scale-95 flex items-center gap-2">
              {isAgentRunning ? "[ PROCESSING ]" : "TRIGGER EVENT v"}
            </button>
            <div className="absolute right-0 mt-2 w-64 bg-gray-800 border border-red-900 rounded-md shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
              <div className="p-2 flex flex-col gap-1">
                {chaosScenarios.map((scenario, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleChaos(scenario)}
                    disabled={isAgentRunning}
                    className="text-left px-4 py-3 hover:bg-gray-700 rounded flex flex-col disabled:opacity-50"
                  >
                    <span className="font-bold text-sm text-red-400">{scenario.type}</span>
                    <span className="text-xs text-gray-400">@ {scenario.location} | Severity: {scenario.severity}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* DEDICATED APPROVAL LIST */}
      {pendingApprovals.length > 0 && (
        <div className="mb-8 p-6 bg-yellow-900/30 border border-yellow-600 rounded-lg shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-2xl font-bold text-yellow-500">[ACTION REQUIRED] Human Authorization</h2>
              <p className="text-yellow-200 text-sm mt-1">
                The AI agent has halted autonomous execution due to a High-Severity event. {pendingApprovals.length} shipments require your approval to reroute.
              </p>
            </div>
            <button
              onClick={handleApprove}
              className="px-8 py-3 bg-yellow-600 hover:bg-yellow-500 text-black font-bold rounded shadow-lg transition-transform animate-pulse"
            >
              VERIFY & EXECUTE REROUTE
            </button>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {pendingApprovals.map((s: any) => (
              <div key={s.shipment_id} className="bg-gray-900 p-2 rounded border border-yellow-700 text-xs whitespace-nowrap">
                <span className="text-yellow-500 font-mono">{s.shipment_id}</span> | {s.carrier}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">

          {/* TRIGGERED ALERTS LOG */}
          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-red-900/50">
            <h2 className="text-xl font-semibold mb-4 text-red-400">Active Disruption Alerts</h2>
            {alerts.length === 0 ? (
              <p className="text-gray-500 italic">No active disruptions detected.</p>
            ) : (
              <ul className="space-y-3">
                {alerts.map((a: any) => (
                  <li key={a.id} className="bg-red-900/20 border border-red-700/50 p-3 rounded flex justify-between items-center">
                    <div>
                      <strong className="text-red-400">{a.type}</strong> @ {a.location} - <span className="text-red-200">{a.description}</span>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      a.severity === 'High' ? 'bg-red-600' : a.severity === 'Medium' ? 'bg-orange-500' : 'bg-yellow-500 text-black'
                    }`}>
                      {a.severity}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-blue-300">Global Shipment Status</h2>
                <span className="text-sm text-gray-400">Tracking: {shipments.length}</span>
            </div>

            <div className="overflow-x-auto min-h-[400px]">
              <table className="w-full text-left text-sm">
                <thead className="text-gray-400 border-b border-gray-700">
                  <tr>
                    <th className="pb-2">ID</th>
                    <th className="pb-2">Route</th>
                    <th className="pb-2">Carrier</th>
                    <th className="pb-2">Risk Status</th>
                  </tr>
                </thead>
                <tbody>
                  {currentShipments.map((s: any) => {
                    const isAffected = activeAlertLocations.includes(s.origin) || activeAlertLocations.includes(s.destination);
                    return (
                      <tr key={s.shipment_id} className="border-b border-gray-700/50">
                        <td className="py-3 font-mono">
                            {isAffected && <span title="Affected by Alert" className="text-red-500 mr-2">[!]</span>}
                            {s.shipment_id}
                        </td>
                        <td className="py-3">{s.origin} → {s.destination}</td>
                        <td className="py-3">{s.carrier}</td>
                        <td className="py-3">
                          <span className={`px-2 py-1 rounded text-xs font-bold ${
                            s.status === "Pending Approval" ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/50" :
                            s.status.includes("Auto") ? "bg-purple-500/20 text-purple-400" :
                            s.status.includes("Approved") ? "bg-green-500/20 text-green-400" :
                            "bg-blue-500/20 text-blue-400"
                          }`}>
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
              <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-700">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded text-sm transition-colors"
                >
                  &lt; Previous
                </button>
                <span className="text-sm text-gray-400">Page {currentPage} of {totalPages}</span>
                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded text-sm transition-colors"
                >
                  Next &gt;
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Action History Log */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700 h-full max-h-[85vh] overflow-y-auto">
          <h2 className="text-xl font-semibold mb-4 text-purple-400">Action History Log</h2>
          {agentLogs.length === 0 ? (
            <p className="text-gray-500 italic">Awaiting system events...</p>
          ) : (
            <div className="space-y-4">
              {agentLogs.map((log: any, idx) => (
                <div key={idx} className={`p-4 rounded border text-sm ${log.hypothesis?.includes("Human") ? 'bg-yellow-900/10 border-yellow-700/50' : 'bg-gray-900 border-gray-700'}`}>
                  <div className="mb-2">
                    <span className="text-xs text-gray-500 uppercase tracking-wide block">Reasoning / Hypothesis</span>
                    <p className="text-gray-300 mt-1">{log.hypothesis}</p>
                  </div>
                  <div className="mb-2">
                    <span className="text-xs text-gray-500 uppercase tracking-wide block">System Decision</span>
                    <p className="text-blue-300 mt-1">{log.decision}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wide block">Execution</span>
                    <p className={`font-semibold mt-1 ${log.action_taken?.includes("human") || log.hypothesis?.includes("Human") ? "text-yellow-400" : "text-purple-400"}`}>
                      {log.action_taken?.includes("human") || log.hypothesis?.includes("Human") ? "[ESCALATED] " : "[AUTO] "} {log.action_taken}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}