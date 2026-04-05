import type { Severity, StatusTone } from "../../lib/theme/tokens";

export type IncidentRecord = {
  id: string;
  title: string;
  priority: Severity;
  state: Exclude<StatusTone, "pending_response" | "disabled">;
  detectionType: string;
  linkedAlertsCount: number;
  primaryAsset: string;
  assignee: string;
  lastUpdated: string;
  sourceType: "Wazuh" | "Suricata";
  summary: string;
};

export type IncidentsListResponse = {
  items: IncidentRecord[];
  total: number;
  generatedAt: string;
};
