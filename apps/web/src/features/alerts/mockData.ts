import type { AlertsListResponse } from "./types";

export const mockAlertsResponse: AlertsListResponse = {
  total: 6,
  generatedAt: "2026-04-05T09:10:00Z",
  items: [
    {
      id: "ALRT-1084",
      detectionType: "brute_force",
      sourceType: "Wazuh",
      severity: "high",
      status: "investigating",
      asset: "edge-auth-01",
      sourceIp: "185.244.25.11",
      destinationPort: "22",
      timestamp: "2026-04-05 08:14:09 UTC",
      riskScore: 87,
      username: "svc-admin",
      eventId: "evt-54fd8c"
    },
    {
      id: "ALRT-1085",
      detectionType: "port_scan",
      sourceType: "Suricata",
      severity: "medium",
      status: "triaged",
      asset: "branch-fw-02",
      sourceIp: "10.88.4.51",
      destinationPort: "3389",
      timestamp: "2026-04-05 08:18:44 UTC",
      riskScore: 61,
      username: "network-watch",
      eventId: "evt-7bc310"
    },
    {
      id: "ALRT-1086",
      detectionType: "unauthorized_user_creation",
      sourceType: "Wazuh",
      severity: "critical",
      status: "pending_response",
      asset: "finance-dc-01",
      sourceIp: "10.42.11.9",
      destinationPort: "389",
      timestamp: "2026-04-05 08:24:17 UTC",
      riskScore: 95,
      username: "unknown-admin",
      eventId: "evt-a190d2"
    },
    {
      id: "ALRT-1087",
      detectionType: "file_integrity_violation",
      sourceType: "Wazuh",
      severity: "high",
      status: "contained",
      asset: "ops-files-03",
      sourceIp: "10.42.7.54",
      destinationPort: "445",
      timestamp: "2026-04-05 08:32:51 UTC",
      riskScore: 79,
      username: "backup-runner",
      eventId: "evt-c8ae24"
    },
    {
      id: "ALRT-1088",
      detectionType: "brute_force",
      sourceType: "Suricata",
      severity: "medium",
      status: "new",
      asset: "vpn-gateway-01",
      sourceIp: "202.129.41.77",
      destinationPort: "443",
      timestamp: "2026-04-05 08:41:12 UTC",
      riskScore: 68,
      username: "vpn-auth",
      eventId: "evt-c42f8d"
    },
    {
      id: "ALRT-1089",
      detectionType: "port_scan",
      sourceType: "Suricata",
      severity: "low",
      status: "resolved",
      asset: "warehouse-edge-02",
      sourceIp: "172.21.8.22",
      destinationPort: null,
      timestamp: "2026-04-05 08:55:03 UTC",
      riskScore: 34,
      username: "sensor-pipeline",
      eventId: "evt-f34dd1"
    }
  ]
};
