export type AssetAgentStatus = "online" | "degraded" | "offline";
export type AssetCriticality = "mission_critical" | "high" | "standard" | "low";

export type AssetRecord = {
  id: string;
  hostname: string;
  ipAddress: string;
  operatingSystem: string;
  agentStatus: AssetAgentStatus;
  criticality: AssetCriticality;
  recentAlertsCount: number;
  lastSeen: string;
  environment: "production" | "office" | "remote";
  openIncidents: number;
};

export type AssetsListResponse = {
  items: AssetRecord[];
  total: number;
  generatedAt: string;
};

export type AssetsListApiResponse = {
  items: Array<{
    id: string;
    hostname: string;
    ip_address: string;
    operating_system: string | null;
    criticality: "low" | "medium" | "high" | "critical";
    created_at: string;
    updated_at: string;
  }>;
};
