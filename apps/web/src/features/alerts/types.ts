/*
 * TypeScript types used by the alerts feature area.
 */
import type { Severity, StatusTone } from "../../lib/theme/tokens";
import type { ListQueryMeta, SortDirection } from "../../lib/api/query";

// Defines the Alerts Date Range data shape used by this frontend module.
export type AlertsDateRange = "4h" | "12h" | "24h" | "all";
// Defines the Alerts Sort Field data shape used by this frontend module.
export type AlertsSortField = "timestamp" | "severity" | "risk_score";
// Defines the Alert Status Filter data shape used by this frontend module.
export type AlertStatusFilter = Extract<
  StatusTone,
  "new" | "triaged" | "investigating" | "contained" | "resolved" | "pending_response"
>;

// Defines the Alerts List Query data shape used by this frontend module.
export type AlertsListQuery = {
  search: string;
  severity: Severity | "";
  status: AlertStatusFilter | "";
  detectionType: string;
  sourceType: "" | "wazuh" | "suricata";
  asset: string;
  dateRange: AlertsDateRange;
  sortBy: AlertsSortField;
  sortDirection: SortDirection;
  page: number;
  pageSize: number;
};

// Defines the Alert Record data shape used by this frontend module.
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

// Defines the Alerts List Response data shape used by this frontend module.
export type AlertsListResponse = {
  items: AlertRecord[];
  total: number;
  generatedAt: string;
  meta: ListQueryMeta;
};

// Defines the Alerts List Api Response data shape used by this frontend module.
export type AlertsListApiResponse = {
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
    detection_type: string;
    source_type: "Wazuh" | "Suricata";
    severity_label: Severity;
    status_label: AlertStatusFilter | "contained";
    asset_name: string | null;
    source_ip: string | null;
    destination_port: number | null;
    created_at: string;
    risk_score_value: number | null;
    username: string | null;
    event_id: string | null;
  }>;
};
