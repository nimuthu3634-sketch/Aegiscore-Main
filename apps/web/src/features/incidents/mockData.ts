import type { IncidentsListResponse } from "./types";

export const mockIncidentsResponse: IncidentsListResponse = {
  total: 5,
  generatedAt: "2026-04-05T09:10:00Z",
  items: [
    {
      id: "INC-301",
      title: "Repeated SSH brute-force targeting edge-auth-01",
      priority: "high",
      state: "investigating",
      detectionType: "brute_force",
      linkedAlertsCount: 6,
      primaryAsset: "edge-auth-01",
      assignee: "N. Silva",
      lastUpdated: "2026-04-05 08:41 UTC",
      sourceType: "Wazuh",
      summary: "Multiple repeated failed SSH attempts from a foreign source address with matching usernames."
    },
    {
      id: "INC-302",
      title: "Unauthorized directory service account creation",
      priority: "critical",
      state: "triaged",
      detectionType: "unauthorized_user_creation",
      linkedAlertsCount: 2,
      primaryAsset: "finance-dc-01",
      assignee: "R. Perera",
      lastUpdated: "2026-04-05 08:29 UTC",
      sourceType: "Wazuh",
      summary: "A new administrative-style account appeared on the finance domain controller outside approved change activity."
    },
    {
      id: "INC-303",
      title: "Branch firewall port scan wave",
      priority: "medium",
      state: "new",
      detectionType: "port_scan",
      linkedAlertsCount: 9,
      primaryAsset: "branch-fw-02",
      assignee: "SOC Queue",
      lastUpdated: "2026-04-05 08:20 UTC",
      sourceType: "Suricata",
      summary: "Lateral-looking scan behavior observed against remote-access ports in the branch firewall segment."
    },
    {
      id: "INC-304",
      title: "File integrity drift on operations share",
      priority: "high",
      state: "contained",
      detectionType: "file_integrity_violation",
      linkedAlertsCount: 4,
      primaryAsset: "ops-files-03",
      assignee: "J. Fernando",
      lastUpdated: "2026-04-05 08:57 UTC",
      sourceType: "Wazuh",
      summary: "Unexpected changes were contained after analyst confirmation on a sensitive operational file share."
    },
    {
      id: "INC-305",
      title: "Edge scan activity resolved by sensor tuning",
      priority: "low",
      state: "resolved",
      detectionType: "port_scan",
      linkedAlertsCount: 3,
      primaryAsset: "warehouse-edge-02",
      assignee: "SOC Queue",
      lastUpdated: "2026-04-05 07:58 UTC",
      sourceType: "Suricata",
      summary: "The incident was closed after sensor behavior was verified and no follow-on activity was found."
    }
  ]
};
