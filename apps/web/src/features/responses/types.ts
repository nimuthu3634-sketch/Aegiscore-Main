export type ResponseMode = "dry-run" | "live";
export type ResponseExecutionStatus = "succeeded" | "warning" | "failed" | "pending";

export type ResponseRecord = {
  id: string;
  actionType: string;
  target: string;
  mode: ResponseMode;
  linkedEntity: string;
  executionStatus: ResponseExecutionStatus;
  executedAt: string;
  resultSummary: string;
};

export type ResponsesListResponse = {
  items: ResponseRecord[];
  total: number;
  generatedAt: string;
};

export type ResponsesListApiResponse = {
  items: Array<{
    id: string;
    action_type: string;
    status: "queued" | "in_progress" | "completed" | "failed";
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
    incident: {
      id: string;
      title: string;
      status: string;
      priority: string;
      created_at: string;
      updated_at: string;
    };
  }>;
};
