import type { Severity, StatusTone } from "../../lib/theme/tokens";
import type { ListQueryMeta, SortDirection } from "../../lib/api/query";

export type IncidentStateFilter = Extract<
  StatusTone,
  "new" | "triaged" | "investigating" | "contained" | "resolved"
>;
export type IncidentsSortField = "updated_at" | "created_at" | "priority";

export type IncidentsListQuery = {
  search: string;
  priority: Severity | "";
  state: IncidentStateFilter | "";
  detectionType: string;
  assignee: string;
  sortBy: IncidentsSortField;
  sortDirection: SortDirection;
  page: number;
  pageSize: number;
};

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
  meta: ListQueryMeta;
};

export type IncidentsListApiResponse = {
  meta: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    sort_by: string;
    sort_direction: SortDirection;
    warnings: string[];
  };
  items: Array<{
    id: string;
    title: string;
    summary: string | null;
    state_label: IncidentStateFilter | "false_positive";
    priority: Severity;
    updated_at: string;
    detection_type: string;
    linked_alerts_count: number;
    primary_asset_name: string | null;
    assignee_name: string | null;
    source_type: "Wazuh" | "Suricata";
  }>;
};
