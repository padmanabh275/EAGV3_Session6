import type { GatewayProviders, GatewayRouters, GatewayStatus, ProjectMeta, RunResponse, StateSummary } from "./types";

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed (${response.status}) for ${url}: ${text}`);
  }
  return (await response.json()) as T;
}

export function fetchProjectMeta(): Promise<ProjectMeta> {
  return requestJson<ProjectMeta>("/api/project-meta");
}

export function runSingleQuery(queryId: string, cleanState: boolean): Promise<RunResponse> {
  return requestJson<RunResponse>("/api/run/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query_id: queryId, clean_state: cleanState }),
  });
}

export function runAllQueries(cleanState: boolean): Promise<RunResponse> {
  return requestJson<RunResponse>("/api/run/all", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ clean_state: cleanState }),
  });
}

export function fetchStateSummary(): Promise<StateSummary> {
  return requestJson<StateSummary>("/api/state/summary");
}

export async function resetState(): Promise<void> {
  await requestJson<{ ok: boolean; message: string }>("/api/state/reset", { method: "POST" });
}

export function fetchGatewayProviders(): Promise<GatewayProviders> {
  return requestJson<GatewayProviders>("/v1/providers");
}

export function fetchGatewayStatus(): Promise<GatewayStatus> {
  return requestJson<GatewayStatus>("/v1/status");
}

export function fetchGatewayRouters(): Promise<GatewayRouters> {
  return requestJson<GatewayRouters>("/v1/routers");
}
