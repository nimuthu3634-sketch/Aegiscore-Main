import type { AnalystNote } from "../../../components/data-display/AnalystNotesPanel";
import type { LinkedAlertRow } from "../../../components/data-display/LinkedAlertsTable";
import type { TimelineItem } from "../../../components/data-display/ActivityTimeline";
import type { RelatedResponseItem } from "../../../components/data-display/RelatedResponsesPanel";
import type { Severity, StatusTone } from "../../../lib/theme/tokens";
import type { AssetCriticality } from "../../assets/types";

export type IncidentAssetSummary = {
  hostname: string;
  ipAddress: string;
  criticality: AssetCriticality;
  recentAlertsCount: number;
};

export type IncidentPriorityExplanation = {
  label: string;
  summary: string;
  rationale: string;
  factors: string[];
  rollupScore: number | null;
  linkedAlertsCount: number;
  scoringMethods: string[];
};

export type IncidentNotificationItem = {
  id: string;
  channel: string;
  deliveryMode: string;
  triggerType: string;
  triggerValue: string;
  recipient: string;
  subject: string;
  status: string;
  createdAt: string;
  sentAt: string;
  errorMessage: string | null;
};

export type IncidentDetailRecord = {
  id: string;
  title: string;
  summary: string;
  priority: Severity;
  state: Exclude<StatusTone, "pending_response" | "disabled">;
  assignee: string;
  createdAt: string;
  updatedAt: string;
  primaryAsset: string;
  detectionType: string;
  linkedAlertsCount: number;
  sourceType: "Wazuh" | "Suricata";
  linkedAlerts: LinkedAlertRow[];
  primaryAssetSummary: IncidentAssetSummary;
  affectedAssets: IncidentAssetSummary[];
  timeline: TimelineItem[];
  notes: AnalystNote[];
  relatedResponses: RelatedResponseItem[];
  correlationExplanation: string;
  groupedEvidence: string[];
  priorityExplanation: IncidentPriorityExplanation;
  availableActions?: string[];
  notifications: IncidentNotificationItem[];
};

export type IncidentDetailResponse = {
  incident: IncidentDetailRecord;
  fetchedAt: string;
};

export type IncidentDetailApiResponse = {
  id: string;
  title: string;
  summary: string | null;
  priority: Severity;
  state: "new" | "triaged" | "investigating" | "contained" | "resolved" | "false_positive";
  assignee: {
    id: string;
    username: string;
    full_name: string | null;
    role: {
      id: string;
      name: string;
    };
  } | null;
  created_at: string;
  updated_at: string;
  primary_asset: {
    id: string;
    hostname: string;
    ip_address: string;
    operating_system: string | null;
    criticality: "low" | "medium" | "high" | "critical";
    created_at: string;
    updated_at: string;
  } | null;
  affected_assets: Array<{
    id: string;
    hostname: string;
    ip_address: string;
    operating_system: string | null;
    criticality: "low" | "medium" | "high" | "critical";
    created_at: string;
    updated_at: string;
  }>;
  linked_alerts: Array<{
      id: string;
      title: string;
      detection_type: string;
      source_type: string;
      severity: Severity;
      status: StatusTone;
    risk_score: number | null;
    timestamp: string;
    asset_hostname: string | null;
    source_ip: string | null;
    destination_ip: string | null;
    destination_port: number | null;
    username: string | null;
  }>;
  grouped_evidence: {
    summary: string;
    evidence_items: string[];
    correlation_keys: Record<string, unknown>;
  };
  response_history: Array<{
    id: string;
    action_type: string;
    status: string;
    policy_name?: string | null;
    target: string | null;
    mode: string | null;
    result_summary: string | null;
    result_message?: string | null;
    attempt_count?: number | null;
    details: Record<string, unknown>;
    created_at: string;
    executed_at: string | null;
    requested_by: {
      id: string;
      username: string;
      full_name: string | null;
      role: {
        id: string;
        name: string;
      };
    } | null;
  }>;
  notifications: Array<{
    id: string;
    channel: string;
    delivery_mode: string;
    trigger_type: string;
    trigger_value: string;
    recipient: string;
    subject: string;
    status: string;
    error_message: string | null;
    created_at: string;
    sent_at: string | null;
  }>;
  analyst_notes: Array<{
    id: string;
    author: {
      id: string;
      username: string;
      full_name: string | null;
      role: {
        id: string;
        name: string;
      };
    } | null;
    content: string;
    created_at: string;
  }>;
  timeline: Array<{
    id: string;
    timestamp: string;
    category: string;
    title: string;
    description: string | null;
    actor: {
      id: string;
      username: string;
      full_name: string | null;
      role: {
        id: string;
        name: string;
      };
    } | null;
    details: Record<string, unknown>;
  }>;
  priority_explanation: {
    label: string;
    summary: string;
    rationale: string;
    factors: string[];
    rollup_score?: number | null;
    linked_alerts_count?: number;
    scoring_methods?: string[];
  };
  state_transition_capabilities: {
    current_state: "new" | "triaged" | "investigating" | "contained" | "resolved" | "false_positive";
    available_actions: string[];
    allowed_target_states: Array<
      "new" | "triaged" | "investigating" | "contained" | "resolved" | "false_positive"
    >;
  };
};

export type IncidentTransitionApiResponse = {
  incident_id: string;
  previous_state: string;
  current_state: string;
  message: string;
};

export type IncidentAnalystNoteCreateApiResponse = {
  note: IncidentDetailApiResponse["analyst_notes"][number];
  message: string;
};
