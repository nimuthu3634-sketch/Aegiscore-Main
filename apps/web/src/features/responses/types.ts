import type { ListQueryMeta, SortDirection } from "../../lib/api/query";

export type ResponseMode = "dry-run" | "live";
export type ResponseExecutionStatus = "succeeded" | "warning" | "failed" | "pending";
export type ResponsesSortField = "executed_at" | "status";

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
};

export type ResponsesListResponse = {
  items: ResponseRecord[];
  total: number;
  generatedAt: string;
  meta: ListQueryMeta;
};

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
    created_at: string;
    executed_at: string | null;
    incident: {
      id: string;
      title: string;
    };
  }>;
};
