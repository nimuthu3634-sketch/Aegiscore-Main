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
