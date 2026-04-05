import type { AnalystNote } from "../../../components/data-display/AnalystNotesPanel";
import type { RelatedResponseItem } from "../../../components/data-display/RelatedResponsesPanel";
import type { KeyValueItem } from "../../../components/data-display/KeyValueGrid";
import type { Severity, StatusTone } from "../../../lib/theme/tokens";

export type AlertScoreExplanation = {
  score: number | null;
  label: string;
  summary: string;
  rationale: string;
  factors: string[];
  drivers: string[];
  scoringMethod?: string | null;
  version?: string | null;
  confidence?: number | null;
};

export type AlertAuditHistoryItem = {
  id: string;
  timestamp: string;
  category: string;
  title: string;
  description: string | null;
  actor: string;
};

export type AlertDetailRecord = {
  id: string;
  title?: string;
  detectionType: string;
  sourceType: "Wazuh" | "Suricata";
  severity: Severity;
  status: StatusTone;
  riskScore: number | null;
  priorityLabel?: Severity | null;
  linkedIncidentId: string | null;
  linkedIncidentTitle?: string | null;
  asset: string;
  sourceIp: string | null;
  destinationIp: string | null;
  destinationPort: string | null;
  username: string | null;
  timestamp: string;
  ruleId: string | null;
  sourceRule: string | null;
  normalizedSummary: string;
  normalizedDetails: KeyValueItem[];
  rawPayload: Record<string, unknown>;
  scoreExplanation: AlertScoreExplanation | null;
  relatedResponses: RelatedResponseItem[];
  notes: AnalystNote[];
  auditHistory?: AlertAuditHistoryItem[];
};

export type AlertDetailResponse = {
  alert: AlertDetailRecord;
  fetchedAt: string;
};

export type AlertDetailApiResponse = {
  id: string;
  title: string;
  description: string | null;
  detection_type: string;
  source_type: string;
  severity: Severity;
  severity_score: number;
  status: StatusTone;
  status_label: StatusTone;
  risk_score: number | null;
  risk_confidence: number | null;
  priority_label: Severity | null;
  linked_incident: {
    id: string;
    title: string;
    status: string;
    priority: string;
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
  } | null;
  asset: {
    id: string;
    hostname: string;
    ip_address: string;
    operating_system: string | null;
    criticality: string;
    created_at: string;
    updated_at: string;
  } | null;
  source_ip: string | null;
  destination_ip: string | null;
  destination_port: number | null;
  username: string | null;
  timestamp: string;
  source_rule: {
    rule_id: string | null;
    name: string | null;
    provider: string | null;
    metadata: Record<string, unknown>;
  } | null;
  normalized_details: Record<string, unknown>;
  raw_payload: Record<string, unknown>;
  score_explanation: {
    label: string;
    summary: string;
    rationale: string;
    factors: string[];
    confidence: number | null;
    scoring_method?: string | null;
    baseline_version?: string | null;
    model_version?: string | null;
    drivers?: Array<{
      label?: string;
      contribution?: number;
      feature?: string;
    }> | null;
  } | null;
  related_responses: Array<{
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
  audit_history: Array<{
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
};

export type AlertLifecycleApiResponse = {
  alert_id: string;
  previous_status: string;
  current_status: string;
  linked_incident_id: string | null;
  message: string;
};

export type AlertLinkIncidentApiResponse = {
  incident_id: string;
  title: string;
  state: string;
  priority: string;
  linked_alerts_count: number;
  message: string;
};

export type AlertLinkIncidentApiRequest = {
  incident_id?: string;
  create_new?: boolean;
  title?: string;
  summary?: string;
};

export type AnalystNoteCreateApiResponse = {
  note: AlertDetailApiResponse["analyst_notes"][number];
  message: string;
};
