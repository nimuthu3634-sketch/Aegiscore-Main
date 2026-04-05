import type { ReactNode } from "react";
import { DataTable, type TableColumn } from "../../../components/data-display/DataTable";
import type { ResponseRecord } from "../types";
import {
  ExecutionStatusBadge,
  ModeBadge
} from "./ResponseBadges";
import { Badge } from "../../../components/ui/Badge";
import { formatTokenLabel } from "../../../lib/formatters";

type ResponsesTableProps = {
  responses: ResponseRecord[];
  footer?: ReactNode;
};

const columns: TableColumn<ResponseRecord>[] = [
  {
    id: "response_id",
    header: "Response ID",
    cell: (row) => <span className="type-mono-sm">{row.id}</span>
  },
  {
    id: "policy_action",
    header: "Policy / action",
    cell: (row) => (
      <div className="space-y-2">
        <p className="text-body-sm font-medium text-content-primary">
          {formatTokenLabel(row.actionType)}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {row.policyName ? <Badge tone="brand">{row.policyName}</Badge> : null}
          <span className="type-mono-sm">{row.actionType}</span>
        </div>
      </div>
    )
  },
  {
    id: "target",
    header: "Target",
    cell: (row) => <span className="type-mono-sm">{row.target}</span>
  },
  {
    id: "mode",
    header: "Mode",
    cell: (row) => <ModeBadge mode={row.mode} />
  },
  {
    id: "linked",
    header: "Linked incident",
    cell: (row) => (
      <div className="space-y-1">
        <p className="text-body-sm font-medium text-content-primary">
          {row.linkedEntityTitle}
        </p>
        <p className="type-mono-sm">{row.linkedEntity}</p>
      </div>
    )
  },
  {
    id: "status",
    header: "Execution",
    cell: (row) => (
      <div className="space-y-2">
        <ExecutionStatusBadge status={row.executionStatus} />
        <p className="type-mono-sm">{row.attemptCount} attempt(s)</p>
      </div>
    )
  },
  {
    id: "summary",
    header: "Outcome",
    cell: (row) => (
      <div className="space-y-2">
        <p className="type-mono-sm">{row.executedAt}</p>
        <p className="text-body-sm text-content-secondary">{row.resultSummary}</p>
        {row.resultMessage && row.resultMessage !== row.resultSummary ? (
          <p className="text-body-sm text-content-muted">{row.resultMessage}</p>
        ) : null}
      </div>
    )
  }
];

export function ResponsesTable({ responses, footer }: ResponsesTableProps) {
  return (
    <DataTable
      ariaLabel="Response history table"
      columns={columns}
      data={responses}
      rowKey={(row) => row.id}
      dense
      footer={footer}
    />
  );
}
