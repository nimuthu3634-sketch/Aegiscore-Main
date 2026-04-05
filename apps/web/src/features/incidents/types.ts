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

export type IncidentsListApiResponse = {
  items: Array<{
    id: string;
    title: string;
    summary: string | null;
    status: "open" | "investigating" | "resolved";
    priority: Severity;
    created_at: string;
    updated_at: string;
    assigned_user: {
      id: string;
      username: string;
      full_name: string | null;
      role: {
        id: string;
        name: string;
      };
    } | null;
    alert: {
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
    };
  }>;
};
