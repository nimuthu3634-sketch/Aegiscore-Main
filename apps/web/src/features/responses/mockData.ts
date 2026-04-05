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
      policyName: "Disable high-risk unauthorized user creation",
      target: "unknown-admin",
      mode: "live",
      linkedEntity: "INC-302",
      linkedEntityTitle: "Unauthorized privileged account on finance domain controller",
      executionStatus: "succeeded",
      executedAt: "2026-04-05 08:33 UTC",
      resultSummary: "Directory account disabled after analyst approval.",
      resultMessage: "Policy execution completed successfully against the targeted identity.",
      attemptCount: 1
    },
    {
      id: "RSP-502",
      actionType: "block_ip",
      policyName: "Dry-run brute force IP block",
      target: "185.244.25.11",
      mode: "dry-run",
      linkedEntity: "ALRT-1084",
      linkedEntityTitle: "Repeated SSH authentication pressure",
      executionStatus: "warning",
      executedAt: "2026-04-05 08:36 UTC",
      resultSummary: "Simulation indicates firewall rule impact on remote admin access.",
      resultMessage: "Dry-run evaluation flagged possible overlap with remote admin access paths.",
      attemptCount: 1
    },
    {
      id: "RSP-503",
      actionType: "quarantine_host_flag",
      policyName: "Contain critical file integrity violations",
      target: "ops-files-03",
      mode: "live",
      linkedEntity: "INC-304",
      linkedEntityTitle: "Critical file integrity violation on operations share",
      executionStatus: "succeeded",
      executedAt: "2026-04-05 08:50 UTC",
      resultSummary: "Host isolated from east-west traffic during containment.",
      resultMessage: "Containment flag was set and the host was queued for isolation follow-up.",
      attemptCount: 1
    },
    {
      id: "RSP-504",
      actionType: "create_manual_review",
      policyName: "Manual review for identity-impacting alerts",
      target: "svc-admin",
      mode: "live",
      linkedEntity: "ALRT-1086",
      linkedEntityTitle: "Unexpected privileged account creation",
      executionStatus: "pending",
      executedAt: "2026-04-05 08:54 UTC",
      resultSummary: "Awaiting analyst confirmation and identity review.",
      resultMessage: "The workflow created a queued manual review task for analyst approval.",
      attemptCount: 1
    },
    {
      id: "RSP-505",
      actionType: "notify_admin",
      policyName: "Notify on external auth pressure",
      target: "202.129.41.77",
      mode: "live",
      linkedEntity: "ALRT-1088",
      linkedEntityTitle: "VPN brute-force burst on gateway",
      executionStatus: "failed",
      executedAt: "2026-04-05 08:57 UTC",
      resultSummary: "Admin notification failed after mail delivery was rejected.",
      resultMessage: "SMTP relay returned a transient failure while dispatching the notification.",
      attemptCount: 2
    },
    {
      id: "RSP-506",
      actionType: "create_manual_review",
      policyName: "Review low-confidence port scan tuning cases",
      target: "port_scan_noise_filter",
      mode: "dry-run",
      linkedEntity: "INC-305",
      linkedEntityTitle: "Low-noise warehouse scan review",
      executionStatus: "succeeded",
      executedAt: "2026-04-05 07:43 UTC",
      resultSummary: "Report-only validation completed for the sensor tuning workflow.",
      resultMessage: "Dry-run confirmed a manual review would be created without live side effects.",
      attemptCount: 1
    }
  ]
};
