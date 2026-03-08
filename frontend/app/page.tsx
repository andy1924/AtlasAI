"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";
import * as topojson from "topojson-client";

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
  details: Array<{ shipment_id: string; status: string; delay_probability: number; outcome: string }>;
}
interface MLPrediction {
  predicted_reliability: number;
  degradation_probability: number;
  current_reliability: number;
  trend: number;
  is_degrading: boolean;
  is_degraded: boolean;
  risk_flag: string;
  last_updated: string;
  error?: string;
}
interface ForecastDay {
  day: number;
  date: string;
  predicted_reliability: number;
  degradation_probability: number;
  is_degraded: boolean;
  risk_flag: string;
}
interface ShipPosition {
  id: string;
  name: string;
  lat: number;
  lng: number;
  destination: string;
  origin: string;
  status: "normal" | "affected" | "at-risk";
  carrier: string;
  speed: number;
  heading: number;
  cargo: string;
}

const PORTS: Record<string, [number, number]> = {
  "Shanghai": [121.4, 31.2], "Singapore": [103.8, 1.3], "Rotterdam": [4.5, 51.9],
  "Mumbai": [72.8, 18.9], "New York": [-74.0, 40.7], "Los Angeles": [-118.2, 33.7],
  "Tokyo": [139.6, 35.6], "Dubai": [55.3, 25.2], "Hamburg": [9.9, 53.5], "Mombasa": [39.6, -4.0],
};

const BASE_SHIPS: ShipPosition[] = [
  { id:"VS-001", name:"Pacific Horizon",  lat:22.3,  lng:114.2,  destination:"Mumbai",      origin:"Shanghai",     status:"normal",   carrier:"FastFreight", speed:18, heading:225, cargo:"Electronics" },
  { id:"VS-002", name:"Ocean Pioneer",    lat:1.3,   lng:103.8,  destination:"Rotterdam",   origin:"Singapore",    status:"affected", carrier:"OceanEx",     speed:0,  heading:270, cargo:"Containers" },
  { id:"VS-003", name:"Arctic Trader",    lat:51.5,  lng:3.5,    destination:"New York",    origin:"Rotterdam",    status:"normal",   carrier:"FastFreight", speed:22, heading:280, cargo:"Machinery" },
  { id:"VS-004", name:"Southern Cross",   lat:-33.9, lng:18.4,   destination:"Mumbai",      origin:"Cape Town",    status:"at-risk",  carrier:"SeaLine",     speed:14, heading:45,  cargo:"Raw Materials" },
  { id:"VS-005", name:"Golden Gate",      lat:37.8,  lng:-122.4, destination:"Tokyo",       origin:"San Francisco",status:"normal",   carrier:"OceanEx",     speed:20, heading:270, cargo:"Tech Parts" },
  { id:"VS-006", name:"Black Sea Star",   lat:43.0,  lng:28.0,   destination:"Hamburg",     origin:"Odessa",       status:"affected", carrier:"SeaLine",     speed:8,  heading:330, cargo:"Grain" },
  { id:"VS-007", name:"Equator Queen",    lat:0.5,   lng:45.0,   destination:"Mombasa",     origin:"Karachi",      status:"at-risk",  carrier:"GlobalShip",  speed:15, heading:200, cargo:"Textiles" },
  { id:"VS-008", name:"North Star",       lat:55.0,  lng:-15.0,  destination:"Halifax",     origin:"Liverpool",    status:"normal",   carrier:"FastFreight", speed:19, heading:280, cargo:"Consumer Goods" },
  { id:"VS-009", name:"Red Sea Falcon",   lat:14.5,  lng:42.8,   destination:"Suez",        origin:"Aden",         status:"affected", carrier:"GlobalShip",  speed:5,  heading:350, cargo:"Oil Tanker" },
  { id:"VS-010", name:"Atlantic Breeze",  lat:25.0,  lng:-60.0,  destination:"Miami",       origin:"Lisbon",       status:"normal",   carrier:"OceanEx",     speed:21, heading:270, cargo:"Auto Parts" },
  { id:"VS-011", name:"Manila Pride",     lat:14.5,  lng:121.0,  destination:"Los Angeles", origin:"Manila",       status:"at-risk",  carrier:"SeaLine",     speed:12, heading:90,  cargo:"Clothing" },
  { id:"VS-012", name:"Gulf Commander",   lat:26.0,  lng:56.0,   destination:"Rotterdam",   origin:"Dubai",        status:"affected", carrier:"GlobalShip",  speed:0,  heading:315, cargo:"Petroleum" },
];

function ConfidenceMeter({ confidence }: { confidence: number }) {
  const color = confidence >= 75 ? "bg-emerald-500" : confidence >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="mt-2">
      <div className="flex justify-between text-xs text-slate-400 mb-1">
        <span>Agent Confidence</span>
        <span className={confidence >= 75 ? "text-emerald-400" : confidence >= 50 ? "text-amber-400" : "text-red-400"}>{confidence}%</span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full transition-all duration-500 ${color}`} style={{ width: `${confidence}%` }} />
      </div>
    </div>
  );
}

function ActionTypeBadge({ actionType }: { actionType: string }) {
  const styles: Record<string, string> = {
    REROUTE:"bg-blue-500/20 text-blue-400 border-blue-500/50",
    HOLD:"bg-orange-500/20 text-orange-400 border-orange-500/50",
    SWITCH_CARRIER:"bg-cyan-500/20 text-cyan-400 border-cyan-500/50",
    EXPEDITE:"bg-purple-500/20 text-purple-400 border-purple-500/50",
    ESCALATE:"bg-red-500/20 text-red-400 border-red-500/50",
    MONITOR:"bg-slate-500/20 text-slate-400 border-slate-500/50",
    HUMAN_APPROVED:"bg-emerald-500/20 text-emerald-400 border-emerald-500/50",
    EVALUATE:"bg-teal-500/20 text-teal-400 border-teal-500/50",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${styles[actionType] || "bg-slate-700 text-slate-400"}`}>
      {actionType}
    </span>
  );
}

function ShipTrackingMap({ ships, alerts }: { ships: ShipPosition[]; alerts: Alert[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{ ship: ShipPosition; x: number; y: number } | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [worldData, setWorldData] = useState<any>(null);

  useEffect(() => {
    fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json")
      .then(r => r.json()).then(setWorldData).catch(() => {});
  }, []);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth || 900;
    const height = svgRef.current.clientHeight || 420;
    svg.selectAll("*").remove();

    const projection = d3.geoNaturalEarth1().scale(width / 6.3).translate([width / 2, height / 2]);
    const path = d3.geoPath().projection(projection);

    const defs = svg.append("defs");
    const oceanGrad = defs.append("linearGradient").attr("id","oceanGrad").attr("x1","0%").attr("y1","0%").attr("x2","0%").attr("y2","100%");
    oceanGrad.append("stop").attr("offset","0%").attr("style","stop-color:#060e1e;stop-opacity:1");
    oceanGrad.append("stop").attr("offset","100%").attr("style","stop-color:#0a1628;stop-opacity:1");

    svg.append("rect").attr("width",width).attr("height",height).attr("fill","url(#oceanGrad)");

    const graticule = d3.geoGraticule()();
    svg.append("path").datum(graticule).attr("d",path).attr("fill","none").attr("stroke","#1a3a6a").attr("stroke-width",0.3).attr("opacity",0.4);

    if (worldData) {
      const countries = topojson.feature(worldData, worldData.objects.countries);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      svg.selectAll(".country").data((countries as any).features).enter()
        .append("path").attr("class","country")
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .attr("d", path as any)
        .attr("fill","#0d2040").attr("stroke","#1a4070").attr("stroke-width",0.4);
    }

    const alertCoords: Record<string,[number,number]> = {
      "South Kathryntown":[15,5],"Haleview":[-75,25],"Port Elizabeth":[27.9,-33.9],
      "North Sandraberg":[45,11],"Kellyland":[103.8,1.3],"Reedchester":[4.5,51.9],
    };
    alerts.forEach(alert => {
      const coords = alertCoords[alert.location];
      if (!coords) return;
      const pt = projection(coords);
      if (!pt) return;
      for (let r = 1; r <= 3; r++) {
        svg.append("circle").attr("cx",pt[0]).attr("cy",pt[1]).attr("r",r*16)
          .attr("fill","none").attr("stroke","#ef4444").attr("stroke-width",0.8).attr("opacity",0.12/r);
      }
      svg.append("circle").attr("cx",pt[0]).attr("cy",pt[1]).attr("r",6)
        .attr("fill","#ef444440").attr("stroke","#ef4444").attr("stroke-width",1);
    });

    ships.forEach(ship => {
      const dest = PORTS[ship.destination];
      if (!dest) return;
      const start = projection([ship.lng, ship.lat]);
      const end = projection(dest);
      if (!start || !end) return;
      const color = ship.status==="affected" ? "#ef4444" : ship.status==="at-risk" ? "#f97316" : "#22d3ee";
      svg.append("line").attr("x1",start[0]).attr("y1",start[1]).attr("x2",end[0]).attr("y2",end[1])
        .attr("stroke",color).attr("stroke-width",0.8).attr("stroke-dasharray","5 4").attr("opacity",0.25);
    });

    Object.entries(PORTS).forEach(([name, coords]) => {
      const pt = projection(coords);
      if (!pt) return;
      svg.append("circle").attr("cx",pt[0]).attr("cy",pt[1]).attr("r",3)
        .attr("fill","#334155").attr("stroke","#64748b").attr("stroke-width",0.8);
      svg.append("text").attr("x",pt[0]+5).attr("y",pt[1]+3)
        .attr("fill","#64748b").attr("font-size","7.5px").attr("font-family","monospace").text(name);
    });

    ships.forEach(ship => {
      const pt = projection([ship.lng, ship.lat]);
      if (!pt) return;
      const color = ship.status==="affected" ? "#ef4444" : ship.status==="at-risk" ? "#f97316" : "#22d3ee";
      const glow  = ship.status==="affected" ? "#ef444450" : ship.status==="at-risk" ? "#f9731650" : "#22d3ee35";

      svg.append("circle").attr("cx",pt[0]).attr("cy",pt[1]).attr("r",12).attr("fill",glow);

      const g = svg.append("g")
        .attr("transform",`translate(${pt[0]},${pt[1]}) rotate(${ship.heading})`)
        .attr("cursor","pointer")
        .on("mouseenter", (e) => setTooltip({ ship, x: e.clientX, y: e.clientY }))
        .on("mouseleave", () => setTooltip(null));

      g.append("polygon").attr("points","0,-8 5,6 0,3 -5,6")
        .attr("fill",color).attr("stroke","white").attr("stroke-width",0.8);

      if (ship.status !== "normal") {
        svg.append("circle").attr("cx",pt[0]).attr("cy",pt[1]).attr("r",14)
          .attr("fill","none").attr("stroke",color).attr("stroke-width",1.5).attr("opacity",0.5);
      }
    });

  }, [worldData, ships, alerts]);

  return (
    <div className="relative w-full h-full">
      <svg ref={svgRef} className="w-full h-full" />
      <div className="absolute bottom-3 left-3 flex items-center gap-4 px-3 py-2 rounded-lg text-xs"
        style={{ background:"rgba(6,14,30,0.85)", backdropFilter:"blur(8px)", border:"1px solid rgba(30,58,95,0.5)" }}>
        {[["bg-cyan-400","Normal"],["bg-orange-400","At Risk"],["bg-red-500","Chaos Affected"]].map(([c,l]) => (
          <div key={l} className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-full ${c}`} />
            <span className="text-slate-300">{l}</span>
          </div>
        ))}
      </div>
      <div className="absolute top-3 right-3 px-3 py-1.5 rounded-lg text-xs"
        style={{ background:"rgba(6,14,30,0.85)", backdropFilter:"blur(8px)", border:"1px solid rgba(30,58,95,0.5)" }}>
        <span className="text-slate-400">Vessels: </span><span className="text-cyan-400 font-bold">{ships.length}</span>
        <span className="text-slate-600 mx-2">|</span>
        <span className="text-red-400 font-bold">{ships.filter(s=>s.status==="affected").length}</span>
        <span className="text-slate-400"> affected</span>
      </div>
      {tooltip && (
        <div className="fixed z-50 pointer-events-none" style={{ left:tooltip.x+14, top:tooltip.y-10 }}>
          <div className="rounded-xl p-3 shadow-2xl text-xs min-w-48" style={{ background:"#080f1f", border:"1px solid #1e3a5f" }}>
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-2 h-2 rounded-full ${tooltip.ship.status==="affected"?"bg-red-500":tooltip.ship.status==="at-risk"?"bg-orange-400":"bg-cyan-400"}`} />
              <span className="font-bold text-white">{tooltip.ship.name}</span>
            </div>
            <div className="space-y-1 text-slate-300">
              <div><span className="text-slate-500">ID: </span>{tooltip.ship.id}</div>
              <div><span className="text-slate-500">Route: </span>{tooltip.ship.origin} → {tooltip.ship.destination}</div>
              <div><span className="text-slate-500">Carrier: </span>{tooltip.ship.carrier}</div>
              <div><span className="text-slate-500">Speed: </span>{tooltip.ship.speed} kts</div>
              <div><span className="text-slate-500">Cargo: </span>{tooltip.ship.cargo}</div>
              <div className={`mt-1.5 px-2 py-1 rounded text-center font-bold text-xs ${tooltip.ship.status==="affected"?"bg-red-500/20 text-red-400":tooltip.ship.status==="at-risk"?"bg-orange-500/20 text-orange-400":"bg-cyan-500/20 text-cyan-400"}`}>
                {tooltip.ship.status==="affected"?"⚠ CHAOS AFFECTED":tooltip.ship.status==="at-risk"?"⚡ AT RISK":"✓ NOMINAL"}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ProfileMenu() {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setOpen(o => !o)}
        className="flex items-center gap-2.5 px-3 py-2 rounded-xl transition-all duration-200"
        style={{ background:"rgba(15,23,42,0.8)", border:"1px solid rgba(51,65,85,0.8)" }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white shadow-lg"
          style={{ background:"linear-gradient(135deg,#3b82f6,#06b6d4)" }}>A</div>
        <div className="text-left hidden sm:block">
          <div className="text-sm font-semibold text-white leading-none">Aditya</div>
          <div className="text-xs text-slate-400 mt-0.5">Logistics Analyst</div>
        </div>
        <svg className={`w-3.5 h-3.5 text-slate-400 transition-transform ${open?"rotate-180":""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/>
        </svg>
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-xl shadow-2xl z-50 overflow-hidden"
          style={{ background:"#080f1f", border:"1px solid #1e3a5f" }}>
          <div className="p-4 border-b border-slate-800" style={{ background:"linear-gradient(135deg,#0d1f38,#080f1f)" }}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white"
                style={{ background:"linear-gradient(135deg,#3b82f6,#06b6d4)" }}>A</div>
              <div>
                <div className="font-semibold text-white">Aditya</div>
                <div className="text-xs text-slate-400">aditya@atlasai.io</div>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400">Active Session</span>
            </div>
          </div>
          <div className="p-2">
            {[["👤","My Profile"],["⚙️","Settings"],["🔔","Notifications"],["📊","My Reports"]].map(([icon,label]) => (
              <button key={label} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-800 text-sm text-slate-300 hover:text-white transition-colors" onClick={() => setOpen(false)}>
                <span>{icon}</span><span>{label}</span>
              </button>
            ))}
          </div>
          <div className="p-2 border-t border-slate-800">
            <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-red-500/10 text-sm text-red-400 transition-colors" onClick={() => setOpen(false)}>
              <span>🚪</span><span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [shipments,      setShipments]      = useState<Shipment[]>([]);
  const [alerts,         setAlerts]         = useState<Alert[]>([]);
  const [agentLogs,      setAgentLogs]      = useState<AgentLog[]>([]);
  const [liveNews,       setLiveNews]       = useState<NewsItem[]>([]);
  const [carrierStats,   setCarrierStats]   = useState<CarrierStat[]>([]);
  const [outcomeResult,  setOutcomeResult]  = useState<OutcomeResult | null>(null);
  const [isAgentRunning, setIsAgentRunning] = useState(false);
  const [isEvaluating,   setIsEvaluating]   = useState(false);
  const [activeTab,      setActiveTab]      = useState<"logs"|"carriers"|"outcomes">("logs");
  const [currentPage,    setCurrentPage]    = useState(1);
  const [ships,          setShips]          = useState<ShipPosition[]>(BASE_SHIPS);
  const [showMap,        setShowMap]        = useState(true);
  const itemsPerPage = 20;

  const [mlPreds,  setMlPreds]  = useState<Record<string, MLPrediction>>({});
  const [mlReady,  setMlReady]  = useState(false);
  const [fCarrier, setFCarrier] = useState<string | null>(null);
  const [forecast, setForecast] = useState<ForecastDay[]>([]);

  const chaosScenarios: ChaosScenario[] = [
    { type:"Port Bombing",        location:"South Kathryntown", severity:"High",   description:"Critical infrastructure destroyed. Total maritime halt." },
    { type:"Hurricane",           location:"Haleview",          severity:"High",   description:"Category 5 hurricane halting all inbound and outbound traffic." },
    { type:"Traffic Jam",         location:"Port Elizabeth",    severity:"Low",    description:"Severe congestion on main highway causing minor delays." },
    { type:"Piracy Threat",       location:"North Sandraberg",  severity:"Medium", description:"Vessels rerouting due to elevated security risks." },
    { type:"Port Strike",         location:"Kellyland",         severity:"Medium", description:"Port workers strike announced. Partial loading halt expected 48h." },
    { type:"Carrier Degradation", location:"Reedchester",       severity:"Medium", description:"Logistics partner experiencing sudden operational degradation." },
  ];

  // Simulate real-time ship movement
  useEffect(() => {
    const interval = setInterval(() => {
      setShips(prev => prev.map(ship => {
        if (ship.status === "affected") return ship;
        return {
          ...ship,
          lat: Math.max(-80, Math.min(80, ship.lat + (Math.random()-0.5)*0.06*(ship.speed/20))),
          lng: ((ship.lng + (Math.random()-0.5)*0.08*(ship.speed/20) + 180) % 360) - 180,
        };
      }));
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (alerts.length > 0) {
      setShips(prev => prev.map((ship, idx) => ({
        ...ship,
        status: idx%3===0 ? "affected" : idx%4===0 ? "at-risk" : "normal"
      })));
    } else {
      setShips(BASE_SHIPS);
    }
  }, [alerts]);

  const fetchML = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/ml-predictions");
      const data = await res.json();
      if (data.ml_available && data.predictions) { setMlPreds(data.predictions); setMlReady(true); }
    } catch {}
  };

  const fetchForecast = async (carrier: string) => {
    if (fCarrier === carrier) { setFCarrier(null); setForecast([]); return; }
    setFCarrier(carrier);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/ml-forecast/${carrier}?days=3`);
      const data = await res.json();
      if (data.forecast) setForecast(data.forecast);
    } catch {}
  };

  const fetchState = useCallback(async () => {
    try {
      const [sR,aR,nR,cR,hR] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/shipments"),
        fetch("http://127.0.0.1:8000/api/alerts"),
        fetch("http://127.0.0.1:8000/api/news"),
        fetch("http://127.0.0.1:8000/api/carrier-reliability"),
        fetch("http://127.0.0.1:8000/api/agent-history"),
      ]);
      const [sD,aD,nD,cD,hD] = await Promise.all([sR.json(),aR.json(),nR.json(),cR.json(),hR.json()]);
      setShipments(sD.shipments||[]); setAlerts(aD.alerts||[]); setLiveNews(nD.news||[]);
      setCarrierStats(cD.carrier_reliability||[]); setAgentLogs(hD.history||[]);
    } catch(e) { console.error("Failed to fetch state:", e); }
    await fetchML();
  }, []);

  useEffect(() => { fetchState(); }, [fetchState]);

  const handleChaos = async (scenario: ChaosScenario) => {
    await fetch("http://127.0.0.1:8000/api/trigger-chaos", {
      method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(scenario),
    });
    await handleRunAgent();
    setCurrentPage(1);
  };

  const handleRunAgent = async () => {
    setIsAgentRunning(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/run-agent", { method:"POST" });
      const data = await res.json();
      setShipments(data.updated_shipments);
      await fetchState();
    } catch(e) { console.error("Agent run failed:", e); }
    setIsAgentRunning(false);
  };

  const handleApprove = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/approve-actions", { method:"POST" });
      const data = await res.json();
      setShipments(data.updated_shipments);
      await fetchState();
    } catch(e) { console.error("Approval failed:", e); }
  };

  const handleEvaluateOutcomes = async () => {
    setIsEvaluating(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/evaluate-outcomes", { method:"POST" });
      const data = await res.json();
      setOutcomeResult(data.results);
      setActiveTab("outcomes");
      await fetchState();
    } catch(e) { console.error("Evaluation failed:", e); }
    setIsEvaluating(false);
  };

  const activeAlertLocations = alerts.map(a => a.location);
  const pendingApprovals = shipments.filter(s => s.status === "Pending Approval");
  const sortedShipments = [...shipments].sort((a,b) => {
    const p: Record<string,number> = {"At Risk":0,"Pending Approval":1,"On Hold":2,"Carrier Switch Pending":3,"Expedited":4,"Rerouted (Auto)":5,"Rerouted (Approved)":6};
    return (p[a.status]??99)-(p[b.status]??99);
  });
  const totalPages = Math.ceil(sortedShipments.length / itemsPerPage);
  const currentShipments = sortedShipments.slice((currentPage-1)*itemsPerPage, currentPage*itemsPerPage);

  const getStatusStyle = (status: string) => {
    const s: Record<string,string> = {
      "At Risk":"bg-red-500/20 text-red-400 border border-red-500/50",
      "Pending Approval":"bg-amber-500/20 text-amber-400 border border-amber-500/50",
      "Rerouted (Auto)":"bg-purple-500/20 text-purple-400",
      "Rerouted (Approved)":"bg-emerald-500/20 text-emerald-400",
      "On Hold":"bg-orange-500/20 text-orange-400",
      "Carrier Switch Pending":"bg-cyan-500/20 text-cyan-400",
      "Expedited":"bg-pink-500/20 text-pink-400",
      "Monitoring":"bg-slate-500/20 text-slate-400",
    };
    return s[status] || "bg-blue-500/20 text-blue-400";
  };

  const atRiskCount   = shipments.filter(s => s.status==="At Risk").length;
  const pendingCount  = pendingApprovals.length;
  const resolvedCount = shipments.filter(s => ["Rerouted (Auto)","Rerouted (Approved)","On Hold","Expedited","Carrier Switch Pending"].includes(s.status)).length;
  const lastLog       = agentLogs[0];

  const liveBarColor = (v: number) => v>=0.85?"bg-emerald-500":v>=0.80?"bg-amber-500":"bg-red-500";
  const predBarColor = (v: number) => v>=0.85?"bg-purple-500":v>=0.80?"bg-amber-500":"bg-red-500";
  const affectedShips = ships.filter(s=>s.status==="affected").length;
  const atRiskShips   = ships.filter(s=>s.status==="at-risk").length;

  return (
    <div className="min-h-screen text-white" style={{ background:"linear-gradient(160deg,#04090f 0%,#060e1c 50%,#040a15 100%)", fontFamily:"'DM Sans','Inter',system-ui,sans-serif" }}>

      {/* HEADER */}
      <header className="sticky top-0 z-40 px-6 py-3" style={{ background:"rgba(4,9,15,0.95)", backdropFilter:"blur(20px)", borderBottom:"1px solid rgba(20,40,70,0.7)" }}>
        <div className="flex justify-between items-center max-w-screen-2xl mx-auto">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background:"linear-gradient(135deg,#2563eb,#0891b2)" }}>
                <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="white" strokeWidth="1.8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                </svg>
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-slate-900" style={{ animation:"pulse 2s infinite" }} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">AtlasAI</h1>
              <p className="text-xs leading-none" style={{ color:"#4a7aaa" }}>Autonomous Logistics Intelligence</p>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-5 text-xs" style={{ color:"#4a7aaa" }}>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Live Tracking</span>
            </div>
            <div className="h-3 w-px bg-slate-700" />
            <span><span className="text-cyan-400 font-bold">{ships.length}</span> vessels</span>
            <div className="h-3 w-px bg-slate-700" />
            <span><span className="text-red-400 font-bold">{affectedShips}</span> affected</span>
            <div className="h-3 w-px bg-slate-700" />
            <span><span className="text-orange-400 font-bold">{atRiskShips}</span> at risk</span>
          </div>

          <div className="flex items-center gap-2.5">
            <button onClick={handleEvaluateOutcomes} disabled={isEvaluating}
              className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all disabled:opacity-50"
              style={{ background:"rgba(20,184,166,0.12)", border:"1px solid rgba(20,184,166,0.35)", color:"#2dd4bf" }}>
              {isEvaluating ? "⟳ Evaluating..." : "📊 Evaluate"}
            </button>
            <button onClick={handleRunAgent} disabled={isAgentRunning}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50"
              style={{ background:"linear-gradient(135deg,#1d4ed8,#1e40af)", boxShadow:"0 0 20px rgba(29,78,216,0.35)" }}>
              {isAgentRunning ? "⟳ Processing..." : "▶ Run Agent"}
            </button>
            <div className="relative group z-50">
              <button className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
                style={{ background:"linear-gradient(135deg,#dc2626,#991b1b)", boxShadow:"0 0 20px rgba(220,38,38,0.3)" }}>
                ⚡ Trigger Event ▾
              </button>
              <div className="absolute right-0 mt-2 w-72 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 overflow-hidden z-50"
                style={{ background:"#080f1f", border:"1px solid rgba(220,38,38,0.4)" }}>
                <div className="p-1.5 space-y-0.5">
                  {chaosScenarios.map((sc,idx) => (
                    <button key={idx} onClick={() => handleChaos(sc)} disabled={isAgentRunning}
                      className="w-full text-left px-4 py-3 rounded-lg transition-colors flex flex-col gap-0.5 disabled:opacity-50"
                      style={{ hover:"background:rgba(127,29,29,0.3)" }}
                      onMouseEnter={e => (e.currentTarget.style.background="rgba(127,29,29,0.3)")}
                      onMouseLeave={e => (e.currentTarget.style.background="transparent")}>
                      <span className="font-bold text-sm text-red-400">{sc.type}</span>
                      <span className="text-xs text-slate-400">@ {sc.location} · <span className={sc.severity==="High"?"text-red-400":sc.severity==="Medium"?"text-orange-400":"text-yellow-400"}>{sc.severity}</span></span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <ProfileMenu />
          </div>
        </div>
      </header>

      <div className="max-w-screen-2xl mx-auto px-6 py-5 space-y-5">

        {/* STATS BAR */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label:"Total Tracked", value:shipments.length, color:"text-blue-400", icon:"📦", glow:"rgba(37,99,235,0.15)", border:"rgba(37,99,235,0.3)" },
            { label:"At Risk",       value:atRiskCount,       color:atRiskCount>0?"text-red-400":"text-slate-500",  icon:"🔴", glow:atRiskCount>0?"rgba(220,38,38,0.12)":"transparent", border:atRiskCount>0?"rgba(220,38,38,0.4)":"rgba(30,41,59,0.5)", pulse:atRiskCount>0 },
            { label:"Pending Approval", value:pendingCount,   color:pendingCount>0?"text-amber-400":"text-slate-500", icon:"⏳", glow:pendingCount>0?"rgba(217,119,6,0.12)":"transparent", border:pendingCount>0?"rgba(217,119,6,0.4)":"rgba(30,41,59,0.5)" },
            { label:"Resolved",      value:resolvedCount,     color:"text-emerald-400", icon:"✅", glow:"rgba(16,185,129,0.12)", border:"rgba(16,185,129,0.3)" },
          ].map(stat => (
            <div key={stat.label} className={`rounded-2xl p-4 ${(stat as {pulse?:boolean}).pulse?"animate-pulse":""}`}
              style={{ background:`radial-gradient(ellipse at top left, ${stat.glow}, transparent)`, border:`1px solid ${stat.border}`, backdropFilter:"blur(10px)" }}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase tracking-widest" style={{ color:"#4a7aaa" }}>{stat.label}</span>
                <span className="text-lg">{stat.icon}</span>
              </div>
              <span className={`text-3xl font-bold tracking-tight ${stat.color}`}>{stat.value}</span>
            </div>
          ))}
        </div>

        {/* APPROVAL BANNER */}
        {pendingApprovals.length > 0 && (
          <div className="p-5 rounded-2xl" style={{ background:"rgba(92,40,5,0.25)", border:"1px solid rgba(217,119,6,0.5)", backdropFilter:"blur(10px)" }}>
            <div className="flex justify-between items-center mb-3">
              <div>
                <h2 className="text-lg font-bold text-amber-400">⚠️ Human Authorization Required</h2>
                <p className="text-sm mt-0.5" style={{ color:"rgba(253,230,138,0.7)" }}>
                  Agent halted execution. {pendingApprovals.length} shipment(s) require your approval.
                </p>
                {lastLog && <p className="text-xs mt-1.5 font-mono" style={{ color:"rgba(253,230,138,0.5)" }}>↳ {lastLog.hypothesis?.slice(0,140)}...</p>}
              </div>
              <button onClick={handleApprove}
                className="px-6 py-3 rounded-xl font-bold text-sm flex-shrink-0 animate-pulse"
                style={{ background:"linear-gradient(135deg,#d97706,#b45309)", boxShadow:"0 0 25px rgba(217,119,6,0.4)" }}>
                VERIFY & EXECUTE
              </button>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {pendingApprovals.map(s => (
                <div key={s.shipment_id} className="flex-shrink-0 px-3 py-1.5 rounded-lg text-xs"
                  style={{ background:"rgba(15,23,42,0.6)", border:"1px solid rgba(217,119,6,0.3)" }}>
                  <span className="text-amber-400 font-mono">{s.shipment_id}</span>
                  <span style={{ color:"#64748b" }}> · {s.carrier} · risk: {(s.delay_probability*100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* MAP */}
        <div className="rounded-2xl overflow-hidden" style={{ border:"1px solid rgba(20,40,70,0.8)", boxShadow:"0 25px 50px rgba(0,0,0,0.5)" }}>
          <div className="flex items-center justify-between px-5 py-3.5" style={{ background:"rgba(4,9,15,0.95)", borderBottom:"1px solid rgba(20,40,70,0.7)" }}>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <h2 className="font-semibold text-white">Live Fleet Tracker</h2>
              <span className="text-xs px-2 py-0.5 rounded-full font-semibold" style={{ background:"rgba(16,185,129,0.12)", border:"1px solid rgba(16,185,129,0.3)", color:"#34d399" }}>REAL-TIME</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-3 text-xs" style={{ color:"#4a7aaa" }}>
                <span><span className="text-cyan-400 font-bold">{ships.filter(s=>s.status==="normal").length}</span> nominal</span>
                <span><span className="text-orange-400 font-bold">{atRiskShips}</span> at risk</span>
                <span><span className="text-red-400 font-bold">{affectedShips}</span> affected</span>
              </div>
              <button onClick={() => setShowMap(v=>!v)}
                className="text-xs px-3 py-1.5 rounded-lg transition-all"
                style={{ border:"1px solid rgba(51,65,85,0.7)", color:"#64748b" }}
                onMouseEnter={e => { e.currentTarget.style.color="#e2e8f0"; e.currentTarget.style.borderColor="rgba(100,116,139,0.7)"; }}
                onMouseLeave={e => { e.currentTarget.style.color="#64748b"; e.currentTarget.style.borderColor="rgba(51,65,85,0.7)"; }}>
                {showMap ? "Hide Map" : "Show Map"}
              </button>
            </div>
          </div>
          {showMap && <div style={{ height:"440px", background:"#060e1e" }}><ShipTrackingMap ships={ships} alerts={alerts} /></div>}
        </div>

        {/* MAIN GRID */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">

          {/* LEFT */}
          <div className="xl:col-span-2 space-y-5">

            {/* Alerts */}
            <div className="rounded-2xl p-5" style={{ background:"rgba(4,9,15,0.85)", border:"1px solid rgba(127,29,29,0.4)", backdropFilter:"blur(10px)" }}>
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <h2 className="font-semibold text-red-400">Active Disruption Alerts</h2>
                {alerts.length > 0 && (
                  <span className="ml-auto text-xs px-2 py-0.5 rounded-full font-semibold"
                    style={{ background:"rgba(220,38,38,0.12)", border:"1px solid rgba(220,38,38,0.3)", color:"#f87171" }}>
                    {alerts.length} active
                  </span>
                )}
              </div>
              {alerts.length === 0 ? (
                <p className="text-center py-6 italic text-sm" style={{ color:"#334155" }}>No active disruptions detected.</p>
              ) : (
                <div className="space-y-2">
                  {alerts.map(a => (
                    <div key={a.id} className="rounded-xl p-3.5 flex justify-between items-center"
                      style={{ background:"rgba(127,29,29,0.1)", border:"1px solid rgba(127,29,29,0.35)" }}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <strong className="text-red-400 text-sm">{a.type}</strong>
                          <span className="text-slate-400 text-sm">@ {a.location}</span>
                        </div>
                        <p className="text-xs truncate" style={{ color:"#64748b" }}>{a.description}</p>
                      </div>
                      <span className={`ml-4 flex-shrink-0 px-2.5 py-1 rounded-lg text-xs font-bold ${
                        a.severity==="High"?"bg-red-900/40 text-red-300 border border-red-700/40":
                        a.severity==="Medium"?"bg-orange-900/40 text-orange-300 border border-orange-700/40":
                        "bg-yellow-900/40 text-yellow-300 border border-yellow-700/40"
                      }`}>{a.severity}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Shipment Table */}
            <div className="rounded-2xl p-5" style={{ background:"rgba(4,9,15,0.85)", border:"1px solid rgba(20,40,70,0.6)", backdropFilter:"blur(10px)" }}>
              <div className="flex justify-between items-center mb-4">
                <h2 className="font-semibold text-blue-300">Global Shipment Status</h2>
                <span className="text-xs" style={{ color:"#4a7aaa" }}>Tracking: <span className="text-cyan-400 font-bold">{shipments.length}</span></span>
              </div>
              <div className="overflow-x-auto min-h-96">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b" style={{ borderColor:"rgba(20,40,70,0.6)" }}>
                      {["ID","Route","Carrier","Delay Risk","Status"].map(h => (
                        <th key={h} className="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider" style={{ color:"#334155" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {currentShipments.map(s => {
                      const isAffected = activeAlertLocations.includes(s.origin) || activeAlertLocations.includes(s.destination);
                      return (
                        <tr key={s.shipment_id} className="border-b transition-colors"
                          style={{ borderColor:"rgba(20,40,70,0.35)", background: isAffected?"rgba(127,29,29,0.06)":"transparent" }}
                          onMouseEnter={e => (e.currentTarget.style.background=isAffected?"rgba(127,29,29,0.1)":"rgba(15,23,42,0.4)")}
                          onMouseLeave={e => (e.currentTarget.style.background=isAffected?"rgba(127,29,29,0.06)":"transparent")}>
                          <td className="py-2.5 pr-4 font-mono text-xs">
                            {isAffected && <span className="text-red-500 mr-1">⚠</span>}
                            <span style={{ color: isAffected?"#fca5a5":"#94a3b8" }}>{s.shipment_id}</span>
                          </td>
                          <td className="py-2.5 pr-4 text-xs text-slate-300">{s.origin} → {s.destination}</td>
                          <td className="py-2.5 pr-4 text-xs" style={{ color:"#64748b" }}>{s.carrier}</td>
                          <td className="py-2.5 pr-4">
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-slate-800 rounded-full h-1.5">
                                <div className={`h-1.5 rounded-full ${s.delay_probability>0.6?"bg-red-500":s.delay_probability>0.3?"bg-amber-500":"bg-emerald-500"}`}
                                  style={{ width:`${s.delay_probability*100}%` }} />
                              </div>
                              <span className="text-xs" style={{ color:"#64748b" }}>{(s.delay_probability*100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="py-2.5">
                            <span className={`px-2 py-0.5 rounded-md text-xs font-semibold ${getStatusStyle(s.status)}`}>{s.status}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="flex justify-between items-center mt-4 pt-4" style={{ borderTop:"1px solid rgba(20,40,70,0.5)" }}>
                  <button onClick={() => setCurrentPage(p=>Math.max(p-1,1))} disabled={currentPage===1}
                    className="px-4 py-2 rounded-xl text-sm transition-all disabled:opacity-40"
                    style={{ border:"1px solid rgba(30,41,59,0.8)", color:"#64748b" }}
                    onMouseEnter={e => { if(currentPage>1){ e.currentTarget.style.color="#e2e8f0"; e.currentTarget.style.borderColor="rgba(71,85,105,0.8)"; }}}
                    onMouseLeave={e => { e.currentTarget.style.color="#64748b"; e.currentTarget.style.borderColor="rgba(30,41,59,0.8)"; }}>
                    ← Previous
                  </button>
                  <span className="text-sm" style={{ color:"#4a7aaa" }}>Page <span className="text-white font-semibold">{currentPage}</span> of {totalPages}</span>
                  <button onClick={() => setCurrentPage(p=>Math.min(p+1,totalPages))} disabled={currentPage===totalPages}
                    className="px-4 py-2 rounded-xl text-sm transition-all disabled:opacity-40"
                    style={{ border:"1px solid rgba(30,41,59,0.8)", color:"#64748b" }}
                    onMouseEnter={e => { if(currentPage<totalPages){ e.currentTarget.style.color="#e2e8f0"; e.currentTarget.style.borderColor="rgba(71,85,105,0.8)"; }}}
                    onMouseLeave={e => { e.currentTarget.style.color="#64748b"; e.currentTarget.style.borderColor="rgba(30,41,59,0.8)"; }}>
                    Next →
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT */}
          <div className="flex flex-col gap-5">
            <div className="rounded-2xl flex flex-col overflow-hidden" style={{ maxHeight:"62vh", background:"rgba(4,9,15,0.85)", border:"1px solid rgba(20,40,70,0.6)", backdropFilter:"blur(10px)" }}>
              <div className="flex" style={{ borderBottom:"1px solid rgba(20,40,70,0.6)" }}>
                {(["logs","carriers","outcomes"] as const).map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)}
                    className="flex-1 py-3 text-xs font-semibold uppercase tracking-wider transition-all"
                    style={{
                      color: activeTab===tab ? "#60a5fa" : "#334155",
                      borderBottom: activeTab===tab ? "2px solid #3b82f6" : "2px solid transparent",
                      background: activeTab===tab ? "rgba(37,99,235,0.08)" : "transparent",
                    }}>
                    {tab==="logs"?"🤖 Agent Log":tab==="carriers"?"📦 Carriers":"📊 Outcomes"}
                  </button>
                ))}
              </div>
              <div className="overflow-y-auto p-4 flex-1">
                {activeTab==="logs" && (
                  <div className="space-y-3">
                    {agentLogs.length===0
                      ? <p className="text-center py-10 italic text-sm" style={{ color:"#334155" }}>Awaiting system events...</p>
                      : agentLogs.map((log,idx) => (
                        <div key={idx} className="p-3.5 rounded-xl text-sm" style={{
                          background: log.action_type==="HUMAN_APPROVED"?"rgba(6,78,59,0.15)":log.action_type==="ESCALATE"?"rgba(92,40,5,0.15)":log.action_type==="EVALUATE"?"rgba(15,118,110,0.1)":"rgba(8,17,35,0.6)",
                          border: `1px solid ${log.action_type==="HUMAN_APPROVED"?"rgba(16,185,129,0.25)":log.action_type==="ESCALATE"?"rgba(217,119,6,0.25)":log.action_type==="EVALUATE"?"rgba(20,184,166,0.25)":"rgba(20,40,70,0.5)"}`,
                        }}>
                          <div className="flex justify-between items-center mb-2">
                            <ActionTypeBadge actionType={log.action_type}/>
                            <span className="text-xs" style={{ color:"#334155" }}>{log.timestamp?new Date(log.timestamp).toLocaleTimeString():""}</span>
                          </div>
                          <div className="mb-2">
                            <span className="text-xs uppercase tracking-wide block mb-1" style={{ color:"#334155" }}>Hypothesis</span>
                            <p className="text-xs leading-relaxed text-slate-300">{log.hypothesis}</p>
                          </div>
                          <div className="mb-2">
                            <span className="text-xs uppercase tracking-wide block mb-1" style={{ color:"#334155" }}>Execution</span>
                            <p className={`font-semibold text-xs ${!log.autonomous?"text-amber-400":"text-purple-400"}`}>
                              {!log.autonomous?"👤 [HUMAN] ":"🤖 [AUTO] "}{log.action_taken}
                            </p>
                          </div>
                          <div className="flex justify-between text-xs mt-2" style={{ color:"#334155" }}>
                            <span>Affected: {log.shipments_affected}</span>
                            <span>Severity: {log.severity_level}</span>
                          </div>
                          {log.confidence>0 && log.action_type!=="EVALUATE" && <ConfidenceMeter confidence={log.confidence}/>}
                        </div>
                      ))}
                  </div>
                )}
                {activeTab==="carriers" && (
                  <div className="space-y-3">
                    <div className={`px-3 py-2 rounded-xl text-xs font-semibold tracking-wide ${mlReady?"bg-teal-900/20 border border-teal-700/30 text-teal-300":"bg-slate-800/40 border border-slate-700/40 text-slate-400"}`}>
                      {mlReady?"🧠 LSTM Active — next-day reliability predictions":"⚠️ LSTM not loaded — run: python backend/ml/train.py"}
                    </div>
                    {carrierStats.length===0
                      ? <p className="text-center py-8 italic text-sm" style={{ color:"#334155" }}>Loading carrier data...</p>
                      : carrierStats.map(cs => {
                        const ml=mlPreds[cs.carrier], selected=fCarrier===cs.carrier;
                        return (
                          <div key={cs.carrier} onClick={() => fetchForecast(cs.carrier)}
                            className="rounded-xl cursor-pointer transition-all"
                            style={{ background:selected?"rgba(37,99,235,0.06)":"rgba(8,17,35,0.5)", border:`1px solid ${selected?"rgba(59,130,246,0.5)":"rgba(20,40,70,0.5)"}` }}>
                            <div className="p-3 space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-sm text-white">{cs.carrier}</span>
                                <div className="flex items-center gap-2 text-xs">
                                  {ml&&<span>{ml.risk_flag}</span>}
                                  <span style={{ color:"#64748b" }}>{cs.status}</span>
                                </div>
                              </div>
                              <div>
                                <div className="flex justify-between text-xs mb-1" style={{ color:"#64748b" }}>
                                  <span>Live Reliability</span><span>{(cs.reliability_score*100).toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-1.5">
                                  <div className={`h-1.5 rounded-full ${liveBarColor(cs.reliability_score)} transition-all`} style={{ width:`${cs.reliability_score*100}%` }}/>
                                </div>
                              </div>
                              {ml&&!ml.error&&(
                                <div>
                                  <div className="flex justify-between text-xs mb-1">
                                    <span className="text-purple-400">🧠 LSTM Tomorrow</span>
                                    <span className="flex items-center gap-1.5">
                                      <span className="text-slate-300">{(ml.predicted_reliability*100).toFixed(1)}%</span>
                                      <span className={ml.trend>=0?"text-emerald-400":"text-red-400"}>({ml.trend>=0?"+":""}{(ml.trend*100).toFixed(1)}%)</span>
                                    </span>
                                  </div>
                                  <div className="w-full bg-slate-800 rounded-full h-1.5">
                                    <div className={`h-1.5 rounded-full ${predBarColor(ml.predicted_reliability)} transition-all`} style={{ width:`${ml.predicted_reliability*100}%` }}/>
                                  </div>
                                </div>
                              )}
                              {ml?.is_degraded && <div className="px-2 py-1.5 rounded-lg text-xs text-red-300" style={{ background:"rgba(127,29,29,0.2)", border:"1px solid rgba(127,29,29,0.3)" }}>🔴 LSTM predicts degraded state</div>}
                              {!ml?.is_degraded&&ml?.is_degrading && <div className="px-2 py-1.5 rounded-lg text-xs text-orange-300" style={{ background:"rgba(120,53,15,0.2)", border:"1px solid rgba(120,53,15,0.3)" }}>⚠️ Declining trend detected</div>}
                              <div className="flex justify-between text-xs" style={{ color:"#334155" }}>
                                <span>{cs.delayed_shipments}/{cs.total_shipments} delayed</span>
                                {ml&&<span>Deg prob: {(ml.degradation_probability*100).toFixed(0)}%</span>}
                              </div>
                            </div>
                            {selected&&forecast.length>0&&(
                              <div className="p-3" style={{ borderTop:"1px solid rgba(20,40,70,0.5)", background:"rgba(4,9,15,0.6)" }}>
                                <p className="text-xs font-semibold text-purple-400 mb-2">🧠 3-Day LSTM Forecast</p>
                                <div className="grid grid-cols-3 gap-2">
                                  {forecast.map(f => (
                                    <div key={f.day} className="p-2 rounded-xl text-center" style={{ background:f.is_degraded?"rgba(127,29,29,0.2)":"rgba(8,17,35,0.6)", border:`1px solid ${f.is_degraded?"rgba(127,29,29,0.35)":"rgba(20,40,70,0.5)"}` }}>
                                      <p className="text-xs" style={{ color:"#64748b" }}>{f.date.slice(5)}</p>
                                      <p className={`text-sm font-bold mt-1 ${f.predicted_reliability>=0.85?"text-emerald-400":f.predicted_reliability>=0.80?"text-amber-400":"text-red-400"}`}>{(f.predicted_reliability*100).toFixed(1)}%</p>
                                      <p className="text-xs mt-0.5" style={{ color:"#64748b" }}>{f.risk_flag}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
                {activeTab==="outcomes" && (
                  <div>
                    {!outcomeResult
                      ? <div className="text-center py-12">
                          <div className="text-5xl mb-3">📊</div>
                          <p className="text-sm mb-2" style={{ color:"#4a7aaa" }}>Click &ldquo;Evaluate Outcomes&rdquo; to check past agent actions.</p>
                          <p className="text-xs" style={{ color:"#334155" }}>This closes the LEARN loop — failures recorded in ChromaDB.</p>
                        </div>
                      : <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-3 mb-4">
                            <div className="rounded-xl p-3 text-center" style={{ background:"rgba(6,78,59,0.15)", border:"1px solid rgba(16,185,129,0.25)" }}>
                              <p className="text-2xl font-bold text-emerald-400">{outcomeResult.successful}</p>
                              <p className="text-xs" style={{ color:"#64748b" }}>Successful</p>
                            </div>
                            <div className="rounded-xl p-3 text-center" style={{ background:"rgba(127,29,29,0.15)", border:"1px solid rgba(220,38,38,0.25)" }}>
                              <p className="text-2xl font-bold text-red-400">{outcomeResult.failed}</p>
                              <p className="text-xs" style={{ color:"#64748b" }}>Failed</p>
                            </div>
                          </div>
                          <div className="space-y-2 max-h-56 overflow-y-auto">
                            {outcomeResult.details.map((d,idx) => (
                              <div key={idx} className="p-2.5 rounded-xl text-xs" style={{ background:d.outcome.includes("SUCCESS")?"rgba(6,78,59,0.1)":"rgba(127,29,29,0.1)", border:`1px solid ${d.outcome.includes("SUCCESS")?"rgba(16,185,129,0.2)":"rgba(220,38,38,0.2)"}` }}>
                                <div className="flex justify-between">
                                  <span className="font-mono text-slate-300">{d.shipment_id}</span>
                                  <span>{d.outcome.includes("SUCCESS")?"✅":"❌"}</span>
                                </div>
                                <div className="mt-0.5" style={{ color:"#64748b" }}>{d.status} — risk: {(d.delay_probability*100).toFixed(0)}%</div>
                              </div>
                            ))}
                          </div>
                        </div>
                    }
                  </div>
                )}
              </div>
            </div>

            {/* Live News */}
            <div className="rounded-2xl p-5 overflow-y-auto" style={{ maxHeight:"35vh", background:"rgba(4,9,15,0.85)", border:"1px solid rgba(20,40,70,0.6)", backdropFilter:"blur(10px)" }}>
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                <h2 className="font-semibold text-blue-300">Global Disruption Radar</h2>
              </div>
              {liveNews.length===0
                ? <p className="text-center py-4 italic text-sm" style={{ color:"#334155" }}>Scanning global OSINT feeds...</p>
                : <div className="space-y-2.5">
                    {liveNews.map((item,idx) => (
                      <div key={idx} className="p-3 rounded-xl text-sm" style={{ background:"rgba(8,17,35,0.6)", border:"1px solid rgba(20,40,70,0.5)" }}>
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ background:"rgba(127,29,29,0.2)", color:"#f87171" }}>{item.chaos_type}</span>
                          {item.location&&<span className="text-xs px-1.5 py-0.5 rounded" style={{ background:"rgba(127,29,29,0.15)", color:"#fca5a5", border:"1px solid rgba(127,29,29,0.3)" }}>📍 {item.location}</span>}
                        </div>
                        <a href={item.url} target="_blank" rel="noopener noreferrer"
                          className="text-xs leading-relaxed block transition-colors text-slate-300 hover:text-blue-400">{item.title}</a>
                        <p className="text-xs mt-1.5" style={{ color:"#334155" }}>Source: {item.source}</p>
                      </div>
                    ))}
                  </div>
              }
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs pb-4 pt-2" style={{ borderTop:"1px solid rgba(20,40,70,0.4)", color:"#1e3a5f" }}>
          <span>AtlasAI · Autonomous Logistics Intelligence Layer · v2.1</span>
          <span>Logged in as <span style={{ color:"#4a7aaa" }}>Aditya</span> · Logistics Analyst · Mumbai, IN</span>
        </div>
      </div>
    </div>
  );
}