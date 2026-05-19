export interface ProjectModuleInfo {
  name: string;
  path: string;
  role: string;
}

export interface ProjectMeta {
  title: string;
  summary: string;
  modules: ProjectModuleInfo[];
  constraints: string[];
  commands: string[];
  target_queries: string[];
}

export interface MemoryRecord {
  key: string;
  value: string;
  source_query: string;
  updated_at: string;
}

export interface StateSummary {
  record_count: number;
  records: MemoryRecord[];
  last_updated: string | null;
}

export interface RunResult {
  query_id: string;
  user_query: string;
  iterations: number;
  answer: string;
  passed: boolean;
  max_allowed_iterations: number;
  traces: unknown[];
}

export interface RunResponse {
  results: RunResult[];
  overall_pass: boolean;
  ran_at: string;
}

export interface GatewayProviders {
  order: string[];
  providers: string[];
  models: Record<string, string>;
  shortcuts: Record<string, string>;
}

export interface GatewayStatus {
  order: string[];
  live: Record<string, unknown>;
  today: Record<string, unknown>;
}

export interface GatewayRouters {
  order: string[];
  providers: string[];
  models: Record<string, string>;
  live: Record<string, unknown>;
  today: Record<string, unknown>;
}
