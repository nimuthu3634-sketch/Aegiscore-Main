import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { SeverityChip } from "../../../components/ui/SeverityChip";
import { StatusChip } from "../../../components/ui/StatusChip";
import type { IncidentRecord } from "../types";

type IncidentSummaryPanelProps = {
  incident: IncidentRecord | null;
};

export function IncidentSummaryPanel({ incident }: IncidentSummaryPanelProps) {
  if (!incident) {
    return null;
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <p className="type-label-md">Selected incident</p>
          <CardTitle>{incident.id}</CardTitle>
          <CardDescription>
            Dense queue-first triage with summary context for fast analyst scanning.
          </CardDescription>
        </div>
        <StatusChip status={incident.state} />
      </CardHeader>
      <CardContent className="space-y-5 pt-0">
        <div className="space-y-2">
          <h3 className="type-heading-sm">{incident.title}</h3>
          <p className="type-body-sm">{incident.summary}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <SeverityChip severity={incident.priority} />
          <Badge tone="outline">{incident.sourceType}</Badge>
          <Badge tone="brand">{incident.linkedAlertsCount} linked alerts</Badge>
        </div>
        <div className="space-y-2">
          <p className="type-label-sm">Queue context</p>
          <p className="type-mono-sm">primary_asset: {incident.primaryAsset}</p>
          <p className="type-mono-sm">assignee: {incident.assignee}</p>
          <p className="type-mono-sm">last_updated: {incident.lastUpdated}</p>
          <p className="type-mono-sm">detection: {incident.detectionType}</p>
        </div>
      </CardContent>
    </Card>
  );
}
