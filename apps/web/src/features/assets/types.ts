/*
 * TypeScript types used by the assets feature area.
 */
import type { ListQueryMeta, SortDirection } from "../../lib/api/query";

// Defines the Asset Agent Status data shape used by this frontend module.
export type AssetAgentStatus = "online" | "degraded" | "offline";
// Defines the Asset Criticality data shape used by this frontend module.
export type AssetCriticality = "mission_critical" | "high" | "standard" | "low";
// Defines the Asset Environment data shape used by this frontend module.
export type AssetEnvironment = "production" | "office" | "remote";
// Defines the Assets Sort Field data shape used by this frontend module.
export type AssetsSortField = "hostname" | "last_seen" | "recent_alerts";

// Defines the Assets List Query data shape used by this frontend module.
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

// Defines the Asset Record data shape used by this frontend module.
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

// Defines the Assets List Response data shape used by this frontend module.
export type AssetsListResponse = {
  items: AssetRecord[];
  total: number;
  generatedAt: string;
  meta: ListQueryMeta;
};

// Defines the Assets List Api Response data shape used by this frontend module.
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
