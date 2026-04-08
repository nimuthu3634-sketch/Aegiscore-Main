import type { Severity, StatusTone } from "../../lib/theme/tokens";
import { Badge } from "../ui/Badge";
import { formatTokenLabel } from "../../lib/formatters";
import { DataTable, type TableColumn } from "./DataTable";
import { SeverityChip } from "../ui/SeverityChip";
import { StatusChip } from "../ui/StatusChip";

export type LinkedAlertRow = {
  id: string;
  detectionType: string;
  sourceType: string;
  severity: Severity;
  status: StatusTone;
  asset: string;
  sourceIp: string;
  timestamp: string;
  riskScore: number | null;
  eventId?: string | null;
};

type LinkedAlertsTableProps = {
  alerts: LinkedAlertRow[];
  onRowClick?: (alert: LinkedAlertRow) => void;
};

const columns: TableColumn<LinkedAlertRow>[] = [
  {
    id: "alert",
    header: "Alert",
    cell: (row) => (
      <div className="space-y-1">
        <div className="type-mono-sm">{row.id}</div>
        <div className="type-mono-sm">{row.eventId ?? "event unavailable"}</div>
      </div>
    )
  },
  {
    id: "detection",
    header: "Detection",
    cell: (row) => (
      <div className="space-y-1">
        <div className="text-body-sm font-medium text-content-primary">
          {formatTokenLabel(row.detectionType)}
        </div>
        <Badge tone="outline">{row.sourceType}</Badge>
      </div>
    )
  },
  {
    id: "severity",
    header: "Severity",
    cell: (row) => <SeverityChip severity={row.severity} />
  },
  {
    id: "status",
    header: "State",
    cell: (row) => <StatusChip status={row.status} />
  },
  {
    id: "asset",
    header: "Asset",
    cell: (row) => (
      <div className="space-y-1">
        <div className="text-body-sm font-medium text-content-primary">
          {row.asset}
        </div>
        <div className="type-mono-sm">{row.sourceIp}</div>
      </div>
    )
  },
  {
    id: "timestamp",
    header: "Timestamp",
    cell: (row) => <span className="type-mono-sm">{row.timestamp}</span>
  },
  {
    id: "risk",
    header: "Risk",
    cell: (row) => (
      <span className="text-body-sm font-medium text-content-primary">
        {row.riskScore ?? "n/a"}
      </span>
    ),
    align: "right"
  }
];

export function LinkedAlertsTable({
  alerts,
  onRowClick
}: LinkedAlertsTableProps) {
  return (
    <DataTable
      ariaLabel="Linked alerts table"
      columns={columns}
      data={alerts}
      rowKey={(row) => row.id}
      onRowClick={onRowClick}
      dense
    />
  );
}
