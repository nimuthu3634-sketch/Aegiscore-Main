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
  riskScore: number | null;
  username: string;
  eventId: string;
};

export type AlertsListResponse = {
  items: AlertRecord[];
  total: number;
  generatedAt: string;
};

export type AlertsListApiResponse = {
  items: Array<{
    id: string;
    source: string;
    title: string;
    description: string | null;
    detection_type: string;
    severity: number;
    status: "new" | "investigating" | "resolved";
    normalized_payload: Record<string, unknown>;
    created_at: string;
    asset: {
      id: string;
      hostname: string;
      ip_address: string;
      operating_system: string | null;
      criticality: string;
      created_at: string;
      updated_at: string;
    } | null;
    raw_alert: {
      id: string;
      source: string;
      external_id: string | null;
      detection_type: string;
      severity: number;
      raw_payload: Record<string, unknown>;
      received_at: string;
    };
    risk_score: {
      id: string;
      score: number;
      confidence: number;
      reasoning: string;
      calculated_at: string;
    } | null;
    incident: {
      id: string;
      title: string;
      status: string;
      priority: string;
      created_at: string;
      updated_at: string;
    } | null;
  }>;
};
