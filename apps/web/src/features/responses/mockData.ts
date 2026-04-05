import type { ResponsesListResponse } from "./types";

export const mockResponsesResponse: ResponsesListResponse = {
  total: 6,
  generatedAt: "2026-04-05T09:10:00Z",
  meta: {
    page: 1,
    pageSize: 10,
    total: 6,
    totalPages: 1,
    sortBy: "executed_at",
    sortDirection: "desc",
    warnings: []
  },
  items: [
    {
      id: "RSP-501",
      actionType: "disable_user",
      target: "unknown-admin",
      mode: "live",
      linkedEntity: "INC-302",
      executionStatus: "succeeded",
      executedAt: "2026-04-05 08:33 UTC",
      resultSummary: "Directory account disabled after analyst approval."
    },
    {
      id: "RSP-502",
      actionType: "block_source_ip",
      target: "185.244.25.11",
      mode: "dry-run",
      linkedEntity: "ALRT-1084",
      executionStatus: "warning",
      executedAt: "2026-04-05 08:36 UTC",
      resultSummary: "Simulation indicates firewall rule impact on remote admin access."
    },
    {
      id: "RSP-503",
      actionType: "isolate_host",
      target: "ops-files-03",
      mode: "live",
      linkedEntity: "INC-304",
      executionStatus: "succeeded",
      executedAt: "2026-04-05 08:50 UTC",
      resultSummary: "Host isolated from east-west traffic during containment."
    },
    {
      id: "RSP-504",
      actionType: "reset_password",
      target: "svc-admin",
      mode: "live",
      linkedEntity: "ALRT-1086",
      executionStatus: "pending",
      executedAt: "2026-04-05 08:54 UTC",
      resultSummary: "Awaiting analyst confirmation and identity review."
    },
    {
      id: "RSP-505",
      actionType: "block_source_ip",
      target: "202.129.41.77",
      mode: "live",
      linkedEntity: "ALRT-1088",
      executionStatus: "failed",
      executedAt: "2026-04-05 08:57 UTC",
      resultSummary: "Firewall API rejected the target zone update."
    },
    {
      id: "RSP-506",
      actionType: "disable_rule",
      target: "port_scan_noise_filter",
      mode: "dry-run",
      linkedEntity: "INC-305",
      executionStatus: "succeeded",
      executedAt: "2026-04-05 07:43 UTC",
      resultSummary: "Report-only validation completed for the sensor tuning workflow."
    }
  ]
};
