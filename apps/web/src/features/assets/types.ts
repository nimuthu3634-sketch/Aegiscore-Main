import type { ListQueryMeta, SortDirection } from "../../lib/api/query";

export type AssetAgentStatus = "online" | "degraded" | "offline";
export type AssetCriticality = "mission_critical" | "high" | "standard" | "low";
export type AssetEnvironment = "production" | "office" | "remote";
export type AssetsSortField = "hostname" | "last_seen" | "recent_alerts";

export type AssetsListQuery = {
  search: string;
  status: AssetAgentStatus | "";
  criticality: AssetCriticality | "";
  operatingSystem: string;
  environment: AssetEnvironment | "";
  sortBy: AssetsSortField;
  sortDirection: SortDirection;
  page: number;
  pageSize: number;
};

export type AssetRecord = {
  id: string;
  hostname: string;
  ipAddress: string;
  operatingSystem: string;
  agentStatus: AssetAgentStatus;
  criticality: AssetCriticality;
  recentAlertsCount: number;
  lastSeen: string;
  environment: AssetEnvironment;
  openIncidents: number;
};

export type AssetsListResponse = {
  items: AssetRecord[];
  total: number;
  generatedAt: string;
  meta: ListQueryMeta;
};

export type AssetsListApiResponse = {
  meta: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    sort_by: string;
    sort_direction: SortDirection;
    warnings: string[];
  };
  items: Array<{
    id: string;
    hostname: string;
    ip_address: string;
    operating_system: string | null;
    criticality: "low" | "medium" | "high" | "critical";
    agent_status: AssetAgentStatus;
    recent_alerts_count: number;
    last_seen_at: string | null;
    open_incidents_count: number;
    environment: AssetEnvironment;
  }>;
};
