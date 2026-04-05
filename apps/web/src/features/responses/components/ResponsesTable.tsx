import { DataTable, type TableColumn } from "../../../components/data-display/DataTable";
import type { ResponseRecord } from "../types";
import {
  ExecutionStatusBadge,
  ModeBadge
} from "./ResponseBadges";

type ResponsesTableProps = {
  responses: ResponseRecord[];
};

const columns: TableColumn<ResponseRecord>[] = [
  {
    id: "response_id",
    header: "Response ID",
    cell: (row) => <span className="type-mono-sm">{row.id}</span>
  },
  {
    id: "action_type",
    header: "Action type",
    cell: (row) => (
      <span className="text-body-sm font-medium text-content-primary">
        {row.actionType}
      </span>
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
    header: "Linked entity",
    cell: (row) => <span className="type-mono-sm">{row.linkedEntity}</span>
  },
  {
    id: "status",
    header: "Execution",
    cell: (row) => <ExecutionStatusBadge status={row.executionStatus} />
  },
  {
    id: "executed",
    header: "Executed at",
    cell: (row) => <span className="type-mono-sm">{row.executedAt}</span>
  },
  {
    id: "summary",
    header: "Result summary",
    cell: (row) => <span className="text-body-sm text-content-secondary">{row.resultSummary}</span>
  }
];

export function ResponsesTable({ responses }: ResponsesTableProps) {
  return (
    <DataTable
      ariaLabel="Response history table"
      columns={columns}
      data={responses}
      rowKey={(row) => row.id}
      dense
    />
  );
}
