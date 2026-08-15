import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
  timestamp: string;
  uptime_seconds: number;
}

export interface Container {
  id: string;
  container_id: string;
  name: string;
  image: string;
  host: string;
  status: string;
  cpu_percent: number;
  memory_percent: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  risk_score: number;
  threat_count: number;
  is_privileged: boolean;
  is_critical_asset: boolean;
  first_seen: string;
  last_seen: string;
}

export interface Incident {
  id: string;
  incident_number: number;
  title: string;
  description?: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  status: 'OPEN' | 'INVESTIGATING' | 'CONTAINED' | 'RESOLVED' | 'FALSE_POSITIVE';
  container_id?: string;
  container_name?: string;
  host?: string;
  detection_rule?: string;
  mitre_technique?: string;
  mitre_technique_id?: string;
  anomaly_score?: number;
  risk_factors?: {
    score: number;
    level: string;
    factors: Array<{ name: string; contribution: number; reason: string }>;
  };
  attack_indicators?: string[];
  recommended_actions?: string[];
  evidence?: Record<string, any>;
  first_seen: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsSummary {
  total_containers: number;
  active_containers: number;
  open_incidents: number;
  critical_incidents: number;
  high_risk_containers: number;
  threats_today: number;
  total_events: number;
  detection_rate: number;
  avg_risk_score: number;
  events_by_type: Record<string, number>;
  incidents_by_severity: Record<string, number>;
  incidents_by_status: Record<string, number>;
  recent_threats: Array<{
    id: string;
    incident_number: number;
    title: string;
    severity: string;
    risk_score: number;
    status: string;
    container_name: string;
    created_at: string;
  }>;
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  expected_severity: string;
  expected_rules: string[];
}

export const fetchHealth = async (): Promise<HealthResponse> => {
  const res = await api.get('/health');
  return res.data;
};

export const fetchAnalytics = async (): Promise<AnalyticsSummary> => {
  const res = await api.get('/analytics');
  return res.data;
};

export const fetchThreats = async () => {
  const res = await api.get('/threats');
  return res.data;
};

export const fetchIncidents = async (params?: Record<string, any>): Promise<Incident[]> => {
  const res = await api.get('/incidents', { params });
  return res.data;
};

export const fetchIncidentById = async (id: string): Promise<Incident> => {
  const res = await api.get(`/incidents/${id}`);
  return res.data;
};

export const acknowledgeIncident = async (id: string) => {
  const res = await api.post(`/incidents/${id}/acknowledge`);
  return res.data;
};

export const resolveIncident = async (id: string) => {
  const res = await api.post(`/incidents/${id}/resolve`);
  return res.data;
};

export const fetchContainers = async (): Promise<Container[]> => {
  const res = await api.get('/containers');
  return res.data;
};

export const fetchDemoScenarios = async (): Promise<DemoScenario[]> => {
  const res = await api.get('/demo/scenarios');
  return res.data;
};

export const runDemoSimulation = async (scenarioId: string, containerId?: string) => {
  const res = await api.post(`/demo/simulate/${scenarioId}`, null, {
    params: { container_id: containerId },
  });
  return res.data;
};

export const runAllSimulations = async () => {
  const res = await api.post('/demo/simulate-all');
  return res.data;
};
