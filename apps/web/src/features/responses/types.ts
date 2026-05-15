/*
 * TypeScript types used by the responses feature area.
 */
import type { ListQueryMeta, SortDirection } from "../../lib/api/query";

// Defines the Response Mode data shape used by this frontend module.
export type ResponseMode = "dry-run" | "live";
// Defines the Response Execution Status data shape used by this frontend module.
export type ResponseExecutionStatus = "succeeded" | "warning" | "failed" | "pending";
// Defines the Responses Sort Field data shape used by this frontend module.
export type ResponsesSortField = "executed_at" | "status";

// Defines the Responses List Query data shape used by this frontend module.
export type ResponsesListQuery = {
  search: string;
  actionType: string;
  mode: ResponseMode | "";
  executionStatus: ResponseExecutionStatus | "";
  sortBy: ResponsesSortField;
  sortDirection: SortDirection;
  page: number;
  pageSize: number;
};

// Defines the Response Record data shape used by this frontend module.
export type ResponseRecord = {
  id: string;
  actionType: string;
  policyName: string | null;
  target: string;
  mode: ResponseMode;
  linkedEntity: string;
  linkedEntityTitle: string;
  executionStatus: ResponseExecutionStatus;
  executedAt: string;
  resultSummary: string;
  resultMessage: string | null;
  attemptCount: number;
  /** Short summary of persisted notification deliveries tied to this response (if any). */
  notificationSummary: string | null;
  /** Human-readable line when this row is the built-in ML brute-force IP block. */
  mlBruteBlockSummary: string | null;
};

// Defines the Responses List Response data shape used by this frontend module.
export type ResponsesListResponse = {
  items: ResponseRecord[];
  total: number;
  generatedAt: string;
  meta: ListQueryMeta;
};

// Defines the Responses List Api Response data shape used by this frontend module.
export type ResponsesListApiResponse = {
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
    action_type: string;
    policy_name: string | null;
    execution_status_label: ResponseExecutionStatus;
    target: string | null;
    mode: ResponseMode | null;
    result_summary: string | null;
    result_message: string | null;
    attempt_count: number;
    details: Record<string, unknown>;
    created_at: string;
    executed_at: string | null;
    related_notifications?: Array<{
      id: string;
      status: string;
      recipient: string;
      trigger_type: string;
      delivery_mode: string;
    }>;
    incident: {
      id: string;
      title: string;
    };
  }>;
};
