import { Badge } from "../../../components/ui/Badge";
import { DataTable, type TableColumn } from "../../../components/data-display/DataTable";
import { SeverityChip } from "../../../components/ui/SeverityChip";
import { StatusChip } from "../../../components/ui/StatusChip";
import type { AlertRecord } from "../types";

type AlertsTableProps = {
  alerts: AlertRecord[];
  selectedAlertId?: string;
  onRowClick: (alert: AlertRecord) => void;
};

const columns: TableColumn<AlertRecord>[] = [
  {
    id: "alert_id",
    header: "Alert ID",
    cell: (row) => (
      <div className="space-y-1">
        <div className="type-mono-sm font-medium text-content-primary">{row.id}</div>
        <div className="type-mono-sm">{row.eventId}</div>
      </div>
    )
  },
  {
    id: "detection",
    header: "Detection",
    cell: (row) => (
      <div className="space-y-1">
        <div className="text-body-sm font-medium text-content-primary">
          {row.detectionType}
        </div>
        <div className="type-mono-sm">{row.username}</div>
      </div>
    )
  },
  {
    id: "source_type",
    header: "Source",
    cell: (row) => <Badge tone="outline">{row.sourceType}</Badge>
  },
  {
    id: "severity",
    header: "Severity",
    cell: (row) => <SeverityChip severity={row.severity} />
  },
  {
    id: "status",
    header: "Status",
    cell: (row) => <StatusChip status={row.status} />
  },
  {
    id: "asset",
    header: "Asset",
    cell: (row) => (
      <div className="space-y-1">
        <div className="text-body-sm font-medium text-content-primary">{row.asset}</div>
        <div className="type-mono-sm">{row.sourceIp}</div>
      </div>
    )
  },
  {
    id: "port",
    header: "Dst Port",
    cell: (row) => <span className="type-mono-sm">{row.destinationPort ?? "n/a"}</span>,
    align: "right"
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

export function AlertsTable({
  alerts,
  selectedAlertId,
  onRowClick
}: AlertsTableProps) {
  return (
    <DataTable
      ariaLabel="Alerts table"
      columns={columns}
      data={alerts}
      rowKey={(row) => row.id}
      selectedRowKey={selectedAlertId}
      onRowClick={onRowClick}
      dense
    />
  );
}
