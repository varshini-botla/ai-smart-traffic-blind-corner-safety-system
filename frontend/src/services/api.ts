import type {
  TrafficInputData,
  TrafficAnalysisResponse,
  HistoryEventItem,
  AnalyticsSummary,
  ModelInfo,
} from "../types/traffic";

const API_BASE_URL = "http://localhost:8000";
export const WS_URL = "ws://localhost:8000/ws/traffic";

export async function checkHealth(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function analyzeTraffic(
  payload: TrafficInputData
): Promise<TrafficAnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Unable to process traffic analysis.");
  }
  return res.json();
}

export async function getCurrentStatus(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/current-status`);
  if (!res.ok) throw new Error("Failed to load current status");
  return res.json();
}

export async function getHistory(
  limit: number = 50,
  offset: number = 0,
  riskFilter?: string,
  search?: string
): Promise<{ events: HistoryEventItem[]; total: number }> {
  const params = new URLSearchParams();
  params.set("limit", limit.toString());
  params.set("offset", offset.toString());
  if (riskFilter && riskFilter !== "ALL") {
    params.set("risk_filter", riskFilter);
  }
  if (search) {
    params.set("search", search);
  }

  const res = await fetch(`${API_BASE_URL}/api/history?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to load history events");
  return res.json();
}

export async function getAnalytics(): Promise<AnalyticsSummary> {
  const res = await fetch(`${API_BASE_URL}/api/analytics`);
  if (!res.ok) throw new Error("Failed to load analytics");
  return res.json();
}

export async function getModelInfo(): Promise<ModelInfo> {
  const res = await fetch(`${API_BASE_URL}/api/model-info`);
  if (!res.ok) throw new Error("Failed to load model information");
  return res.json();
}

export async function clearHistory(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/history`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear history");
  return res.json();
}

export async function simulateTraffic(payload: any): Promise<TrafficAnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Unable to process traffic simulation.");
  }
  return res.json();
}
