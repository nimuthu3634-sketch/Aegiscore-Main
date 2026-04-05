import type { ReactNode } from "react";
import { DataTable, type TableColumn } from "../../../components/data-display/DataTable";
import type { AssetRecord } from "../types";
import { AgentStatusBadge, CriticalityBadge } from "./AssetBadges";

type AssetsTableProps = {
  assets: AssetRecord[];
  selectedAssetId?: string;
  onRowClick: (asset: AssetRecord) => void;
  footer?: ReactNode;
};

const columns: TableColumn<AssetRecord>[] = [
  {
    id: "hostname",
    header: "Hostname",
    cell: (row) => (
      <div className="space-y-1">
        <div className="text-body-sm font-medium text-content-primary">{row.hostname}</div>
        <div className="type-mono-sm">{row.id}</div>
      </div>
    )
  },
  {
    id: "ip",
    header: "IP address",
    cell: (row) => <span className="type-mono-sm">{row.ipAddress}</span>
  },
  {
    id: "os",
    header: "Operating system",
    cell: (row) => <span className="text-body-sm text-content-primary">{row.operatingSystem}</span>
  },
  {
    id: "agent_status",
    header: "Agent status",
    cell: (row) => <AgentStatusBadge status={row.agentStatus} />
  },
  {
    id: "criticality",
    header: "Criticality",
    cell: (row) => <CriticalityBadge criticality={row.criticality} />
  },
  {
    id: "alerts",
    header: "Recent alerts",
    cell: (row) => (
      <span className="text-body-sm font-medium text-content-primary">
        {row.recentAlertsCount}
      </span>
    ),
    align: "right"
  },
  {
    id: "last_seen",
    header: "Last seen",
    cell: (row) => <span className="type-mono-sm">{row.lastSeen}</span>
  }
];

export function AssetsTable({
  assets,
  selectedAssetId,
  onRowClick,
  footer
}: AssetsTableProps) {
  return (
    <DataTable
      ariaLabel="Assets table"
      columns={columns}
      data={assets}
      rowKey={(row) => row.id}
      selectedRowKey={selectedAssetId}
      onRowClick={onRowClick}
      dense
      footer={footer}
    />
  );
}
