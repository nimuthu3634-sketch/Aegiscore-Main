import { Button } from "../../../components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../../../components/ui/Card";
import type { ReportTopAsset } from "../types";

type TopAssetsReportPanelProps = {
  assets: ReportTopAsset[];
  onViewAssets: () => void;
};

export function TopAssetsReportPanel({
  assets,
  onViewAssets
}: TopAssetsReportPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="space-y-2">
          <p className="type-label-md">Top affected assets</p>
          <CardTitle>Asset exposure summary</CardTitle>
          <CardDescription>
            Assets with the highest linked alert and incident activity in the current
            report window.
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={onViewAssets}>
          View assets
        </Button>
      </CardHeader>
      <CardContent className="pt-0">
        {assets.length ? (
          <div className="overflow-hidden rounded-panel border border-border-subtle">
            <table className="min-w-full divide-y divide-border-subtle text-left">
              <thead className="bg-surface-subtle/70">
                <tr>
                  <th className="px-4 py-3 type-label-sm">Hostname</th>
                  <th className="px-4 py-3 type-label-sm">IP address</th>
                  <th className="px-4 py-3 text-right type-label-sm">Alerts</th>
                  <th className="px-4 py-3 text-right type-label-sm">Incidents</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/80 bg-surface-subtle/30">
                {assets.map((asset) => (
                  <tr key={asset.assetId}>
                    <td className="px-4 py-3 align-top">
                      <div className="space-y-1">
                        <p className="type-heading-sm">{asset.hostname}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 align-top">
                      <span className="type-mono-sm">{asset.ipAddress}</span>
                    </td>
                    <td className="px-4 py-3 text-right align-top">
                      <span className="type-mono-sm">{asset.alertCount}</span>
                    </td>
                    <td className="px-4 py-3 text-right align-top">
                      <span className="type-mono-sm">{asset.incidentCount}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-panel border border-dashed border-border-subtle bg-surface-subtle/35 px-4 py-5">
            <p className="type-body-sm">
              No asset exposure activity was returned for the selected report window.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
