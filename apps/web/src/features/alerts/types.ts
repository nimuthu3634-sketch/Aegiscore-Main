import type { Severity, StatusTone } from "../../lib/theme/tokens";

export type AlertRecord = {
  id: string;
  detectionType: string;
  sourceType: "Wazuh" | "Suricata";
  severity: Severity;
  status: StatusTone;
  asset: string;
  sourceIp: string;
  destinationPort: string | null;
  timestamp: string;
  riskScore: number;
  username: string;
  eventId: string;
};

export type AlertsListResponse = {
  items: AlertRecord[];
  total: number;
  generatedAt: string;
};
