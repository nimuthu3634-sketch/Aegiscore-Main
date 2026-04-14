import { Button } from "../../../components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../../../components/ui/Card";
import {
  AgentStatusBadge,
  CriticalityBadge
} from "../../assets/components/AssetBadges";
import type { AssetRecord } from "../../assets/types";

type TopAffectedAssetsPanelProps = {
  assets: AssetRecord[];
  onViewAssets: () => void;
};

export function TopAffectedAssetsPanel({
  assets,
  onViewAssets
}: TopAffectedAssetsPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="space-y-2">
          <p className="type-label-md">Top affected assets</p>
          <CardTitle>Asset exposure</CardTitle>
          <CardDescription>
            Hosts with the most alert activity — pair with incidents to prioritize
            review.
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={onViewAssets}>
          View assets
        </Button>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        {assets.length ? (
          assets.map((asset) => (
            <div
              key={asset.id}
              className="rounded-panel border border-border-subtle bg-surface-subtle/40 px-4 py-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="type-mono-sm">{asset.hostname}</span>
                    <AgentStatusBadge status={asset.agentStatus} />
                    <CriticalityBadge criticality={asset.criticality} />
                  </div>
                  <p className="type-body-sm">{asset.operatingSystem}</p>
                </div>
                <span className="type-mono-sm">{asset.lastSeen}</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
                <span className="type-body-sm">
                  IP: <span className="type-mono-sm">{asset.ipAddress}</span>
                </span>
                <span className="type-body-sm">
                  Alerts: <span className="type-mono-sm">{asset.recentAlertsCount}</span>
                </span>
                <span className="type-body-sm">
                  Open incidents: <span className="type-mono-sm">{asset.openIncidents}</span>
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-panel border border-dashed border-border-subtle bg-surface-subtle/35 px-4 py-5">
            <p className="type-body-sm">
              No asset ranking yet. Once endpoints report alerts, the hottest hosts surface
              here.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
