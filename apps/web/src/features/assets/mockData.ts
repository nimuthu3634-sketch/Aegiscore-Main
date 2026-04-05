import type { AssetsListResponse } from "./types";

export const mockAssetsResponse: AssetsListResponse = {
  total: 6,
  generatedAt: "2026-04-05T09:10:00Z",
  items: [
    {
      id: "AST-101",
      hostname: "edge-auth-01",
      ipAddress: "10.42.0.21",
      operatingSystem: "Ubuntu Server 22.04",
      agentStatus: "online",
      criticality: "mission_critical",
      recentAlertsCount: 6,
      lastSeen: "2026-04-05 08:44 UTC",
      environment: "production",
      openIncidents: 1
    },
    {
      id: "AST-102",
      hostname: "finance-dc-01",
      ipAddress: "10.42.11.9",
      operatingSystem: "Windows Server 2022",
      agentStatus: "online",
      criticality: "mission_critical",
      recentAlertsCount: 3,
      lastSeen: "2026-04-05 08:46 UTC",
      environment: "production",
      openIncidents: 1
    },
    {
      id: "AST-103",
      hostname: "branch-fw-02",
      ipAddress: "172.16.4.8",
      operatingSystem: "FortiOS 7.x",
      agentStatus: "degraded",
      criticality: "high",
      recentAlertsCount: 9,
      lastSeen: "2026-04-05 08:34 UTC",
      environment: "office",
      openIncidents: 1
    },
    {
      id: "AST-104",
      hostname: "ops-files-03",
      ipAddress: "10.42.7.54",
      operatingSystem: "Windows Server 2019",
      agentStatus: "online",
      criticality: "high",
      recentAlertsCount: 4,
      lastSeen: "2026-04-05 08:52 UTC",
      environment: "production",
      openIncidents: 1
    },
    {
      id: "AST-105",
      hostname: "warehouse-edge-02",
      ipAddress: "172.21.8.22",
      operatingSystem: "Debian 12",
      agentStatus: "online",
      criticality: "standard",
      recentAlertsCount: 1,
      lastSeen: "2026-04-05 07:58 UTC",
      environment: "remote",
      openIncidents: 0
    },
    {
      id: "AST-106",
      hostname: "vpn-gateway-01",
      ipAddress: "10.42.0.5",
      operatingSystem: "Ubuntu Server 22.04",
      agentStatus: "offline",
      criticality: "high",
      recentAlertsCount: 2,
      lastSeen: "2026-04-05 06:33 UTC",
      environment: "production",
      openIncidents: 0
    }
  ]
};
