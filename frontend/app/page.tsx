"use client";

import { useState, useEffect } from "react";

export default function Dashboard() {
  const [shipments, setShipments] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [isAgentRunning, setIsAgentRunning] = useState(false);

  // Fetch the latest state from the FastAPI backend
  const fetchState = async () => {
    try {
      const [shipmentRes, alertRes] = await Promise.all([
        fetch("http://localhost:8000/api/shipments"),
        fetch("http://localhost:8000/api/alerts"),
      ]);
      const shipmentData = await shipmentRes.json();
      const alertData = await alertRes.json();
      setShipments(shipmentData.shipments || []);
      setAlerts(alertData.alerts || []);
    } catch (error) {
      console.error("Failed to fetch state:", error);
    }
  };

  // Initial load
  useEffect(() => {
    fetchState();
  }, []);

  // Trigger the Chaos Button API
  const handleChaos = async () => {
    await fetch("http://localhost:8000/api/trigger-chaos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "Port Strike",
        location: "Strait of Hormuz",
        description: "Unexpected total blockage. All vessels halted.",
      }),
    });
    fetchState();
  };

  // Run the LangGraph Agent
  const handleRunAgent = async () => {
    setIsAgentRunning(true);
    try {
      const res = await fetch("http://localhost:8000/api/run-agent", {
        method: "POST",
      });
      const data = await res.json();
      setAgentLogs((prev) => [data.log, ...prev]);
      setShipments(data.updated_shipments);
    } catch (error) {
      console.error("Failed to run agent:", error);
    }
    setIsAgentRunning(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8 font-sans">
      <header className="flex justify-between items-center mb-8 border-b border-gray-700 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-blue-400">Cyber Cypher</h1>
          <p className="text-gray-400 text-sm">Autonomous Logistics Intelligence</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={handleChaos}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded shadow-lg transition-transform active:scale-95"
          >
            ⚠️ Inject Chaos
          </button>
          <button
            onClick={handleRunAgent}
            disabled={isAgentRunning}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold rounded shadow-lg transition-transform active:scale-95"
          >
            {isAgentRunning ? "🧠 Agent Thinking..." : "🚀 Run AI Agent"}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Live Logistics Data */}
        <div className="col-span-2 space-y-6">
          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
            <h2 className="text-xl font-semibold mb-4 text-blue-300">Live Shipments</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-gray-400 border-b border-gray-700">
                  <tr>
                    <th className="pb-2">ID</th>
                    <th className="pb-2">Route</th>
                    <th className="pb-2">Carrier</th>
                    <th className="pb-2">ETA (hrs)</th>
                    <th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {shipments.map((s: any) => (
                    <tr key={s.shipment_id} className="border-b border-gray-700/50">
                      <td className="py-3 font-mono">{s.shipment_id}</td>
                      <td className="py-3">{s.origin} → {s.destination}</td>
                      <td className="py-3">{s.carrier}</td>
                      <td className="py-3">{s.eta_hours}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs ${
                          s.status === "In Transit" ? "bg-blue-500/20 text-blue-400" : 
                          s.status.includes("Rerouted") ? "bg-orange-500/20 text-orange-400" : 
                          "bg-red-500/20 text-red-400"
                        }`}>
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-red-900/50">
            <h2 className="text-xl font-semibold mb-4 text-red-400">Active Disruption Alerts</h2>
            {alerts.length === 0 ? (
              <p className="text-gray-500 italic">No active disruptions detected.</p>
            ) : (
              <ul className="space-y-3">
                {alerts.map((a: any) => (
                  <li key={a.id} className="bg-red-900/20 border border-red-700/50 p-3 rounded">
                    <strong>{a.type}</strong> @ {a.location} - <span className="text-red-300">{a.description}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right Column: AI Agent Reasoning Log */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700 h-full max-h-[80vh] overflow-y-auto">
          <h2 className="text-xl font-semibold mb-4 text-purple-400">Agent Reasoning Log</h2>
          {agentLogs.length === 0 ? (
            <p className="text-gray-500 italic">Run the AI agent to see its thought process.</p>
          ) : (
            <div className="space-y-6">
              {agentLogs.map((log: any, idx) => (
                <div key={idx} className="bg-gray-900 p-4 rounded border border-gray-700 text-sm">
                  <div className="mb-3">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Observe & Reason</span>
                    <p className="text-gray-300 mt-1">{log.hypothesis}</p>
                  </div>
                  <div className="mb-3">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Decide</span>
                    <p className="text-blue-200 mt-1">{log.decision}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 uppercase tracking-wide">Act</span>
                    <p className="text-green-400 font-semibold mt-1">✓ {log.action_taken}</p>
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