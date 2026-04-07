import type { ReactNode } from "react";
import { DataTable, type TableColumn } from "../../../components/data-display/DataTable";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import { ModeBadge } from "../../responses/components/ResponseBadges";
import type { PolicyRecord } from "../types";
import { formatTokenLabel } from "../../../lib/formatters";

type PoliciesTableProps = {
  policies: PolicyRecord[];
  pendingPolicyId?: string | null;
  onToggle: (policy: PolicyRecord) => void;
  canToggle: boolean;
  footer?: ReactNode;
};

export function PoliciesTable({
  policies,
  pendingPolicyId,
  onToggle,
  canToggle,
  footer
}: PoliciesTableProps) {
  const columns: TableColumn<PolicyRecord>[] = [
    {
      id: "policy",
      header: "Policy",
      cell: (row) => (
        <div className="space-y-1">
          <p className="text-body-sm font-medium text-content-primary">{row.name}</p>
          <p className="text-body-sm text-content-secondary">
            {row.description ?? "Backend-managed automated response policy."}
          </p>
        </div>
      )
    },
    {
      id: "scope",
      header: "Scope",
      cell: (row) => (
        <div className="flex flex-wrap gap-2">
          <Badge tone="outline">{formatTokenLabel(row.target)}</Badge>
          <Badge tone="outline">{formatTokenLabel(row.detectionType)}</Badge>
        </div>
      )
    },
    {
      id: "action",
      header: "Action type",
      cell: (row) => (
        <div className="space-y-1">
          <p className="text-body-sm font-medium text-content-primary">
            {formatTokenLabel(row.actionType)}
          </p>
          <p className="type-mono-sm">{row.actionType}</p>
        </div>
      )
    },
    {
      id: "threshold",
      header: "Threshold",
      cell: (row) => <span className="type-mono-sm">{row.minRiskScore}</span>
    },
    {
      id: "mode",
      header: "Mode",
      cell: (row) => <ModeBadge mode={row.mode} />
    },
    {
      id: "status",
      header: "Enabled",
      cell: (row) => (
        <Badge tone={row.enabled ? "success" : "outline"}>
          {row.enabled ? "enabled" : "disabled"}
        </Badge>
      )
    },
    {
      id: "updated",
      header: "Last updated",
      cell: (row) => <span className="type-mono-sm">{row.lastUpdated}</span>
    },
    {
      id: "controls",
      header: "Action",
      align: "right",
      cell: (row) => (
        <Button
          variant={row.enabled ? "ghost" : "secondary"}
          size="sm"
          data-testid={`policy-toggle-${row.id}`}
          onClick={() => onToggle(row)}
          disabled={!canToggle || pendingPolicyId === row.id}
        >
          {!canToggle
            ? "Admin only"
            : pendingPolicyId === row.id
            ? row.enabled
              ? "Disabling..."
              : "Enabling..."
            : row.enabled
              ? "Disable"
              : "Enable"}
        </Button>
      )
    }
  ];

  return (
    <DataTable
      ariaLabel="Automated response policies table"
      columns={columns}
      data={policies}
      rowKey={(row) => row.id}
      dense
      footer={footer}
    />
  );
}
