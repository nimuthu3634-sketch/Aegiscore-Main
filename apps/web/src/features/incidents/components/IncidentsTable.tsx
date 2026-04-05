import { Badge } from "../../../components/ui/Badge";
import { DataTable, type TableColumn } from "../../../components/data-display/DataTable";
import { SeverityChip } from "../../../components/ui/SeverityChip";
import { StatusChip } from "../../../components/ui/StatusChip";
import type { IncidentRecord } from "../types";

type IncidentsTableProps = {
  incidents: IncidentRecord[];
  selectedIncidentId?: string;
  onRowClick: (incident: IncidentRecord) => void;
};

const columns: TableColumn<IncidentRecord>[] = [
  {
    id: "incident_id",
    header: "Incident ID",
    cell: (row) => <span className="type-mono-sm">{row.id}</span>
  },
  {
    id: "title",
    header: "Title",
    cell: (row) => (
      <div className="space-y-1">
        <div className="text-body-sm font-medium text-content-primary">{row.title}</div>
        <div className="text-body-sm text-content-muted">{row.detectionType}</div>
      </div>
    )
  },
  {
    id: "priority",
    header: "Priority",
    cell: (row) => <SeverityChip severity={row.priority} />
  },
  {
    id: "state",
    header: "State",
    cell: (row) => <StatusChip status={row.state} />
  },
  {
    id: "linked_alerts",
    header: "Linked alerts",
    cell: (row) => (
      <span className="text-body-sm font-medium text-content-primary">
        {row.linkedAlertsCount}
      </span>
    ),
    align: "right"
  },
  {
    id: "primary_asset",
    header: "Primary asset",
    cell: (row) => (
      <div className="space-y-1">
        <div className="text-body-sm font-medium text-content-primary">
          {row.primaryAsset}
        </div>
        <Badge tone="outline">{row.sourceType}</Badge>
      </div>
    )
  },
  {
    id: "assignee",
    header: "Assignee",
    cell: (row) => <span className="type-mono-sm">{row.assignee}</span>
  },
  {
    id: "updated",
    header: "Last updated",
    cell: (row) => <span className="type-mono-sm">{row.lastUpdated}</span>
  }
];

export function IncidentsTable({
  incidents,
  selectedIncidentId,
  onRowClick
}: IncidentsTableProps) {
  return (
    <DataTable
      ariaLabel="Incidents queue table"
      columns={columns}
      data={incidents}
      rowKey={(row) => row.id}
      selectedRowKey={selectedIncidentId}
      onRowClick={onRowClick}
      dense
    />
  );
}
