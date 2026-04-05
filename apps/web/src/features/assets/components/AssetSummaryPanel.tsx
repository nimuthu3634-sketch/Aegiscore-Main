import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import type { AssetRecord } from "../types";
import { AgentStatusBadge, CriticalityBadge } from "./AssetBadges";

type AssetSummaryPanelProps = {
  asset: AssetRecord | null;
};

export function AssetSummaryPanel({ asset }: AssetSummaryPanelProps) {
  if (!asset) {
    return null;
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <p className="type-label-md">Selected asset</p>
          <CardTitle>{asset.hostname}</CardTitle>
          <CardDescription>
            Operational endpoint context stays available alongside the inventory table.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-5 pt-0">
        <div className="flex flex-wrap gap-2">
          <AgentStatusBadge status={asset.agentStatus} />
          <CriticalityBadge criticality={asset.criticality} />
          <Badge tone="outline">{asset.environment}</Badge>
        </div>
        <div className="space-y-2">
          <p className="type-label-sm">Endpoint details</p>
          <p className="type-mono-sm">asset_id: {asset.id}</p>
          <p className="type-mono-sm">ip: {asset.ipAddress}</p>
          <p className="type-mono-sm">os: {asset.operatingSystem}</p>
          <p className="type-mono-sm">last_seen: {asset.lastSeen}</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4">
            <p className="type-label-sm">Recent alerts</p>
            <p className="mt-2 type-heading-md">{asset.recentAlertsCount}</p>
          </div>
          <div className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4">
            <p className="type-label-sm">Open incidents</p>
            <p className="mt-2 type-heading-md">{asset.openIncidents}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
