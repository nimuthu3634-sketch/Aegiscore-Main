import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { SeverityChip } from "../../../components/ui/SeverityChip";
import { StatusChip } from "../../../components/ui/StatusChip";
import type { AlertRecord } from "../types";

type AlertSummaryPanelProps = {
  alert: AlertRecord | null;
};

export function AlertSummaryPanel({ alert }: AlertSummaryPanelProps) {
  if (!alert) {
    return null;
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <p className="type-label-md">Selected alert</p>
          <CardTitle>{alert.id}</CardTitle>
          <CardDescription>
            Row selection is ready for a future detail route without changing the table contract.
          </CardDescription>
        </div>
        <StatusChip status={alert.status} />
      </CardHeader>
      <CardContent className="space-y-5 pt-0">
        <div className="flex flex-wrap gap-2">
          <Badge tone="outline">{alert.sourceType}</Badge>
          <SeverityChip severity={alert.severity} />
          <Badge tone="brand">Risk {alert.riskScore ?? "n/a"}</Badge>
        </div>
        <div className="space-y-3">
          <div>
            <p className="type-label-sm">Detection</p>
            <p className="mt-2 text-body-sm font-medium text-content-primary">
              {alert.detectionType}
            </p>
          </div>
          <div>
            <p className="type-label-sm">Asset</p>
            <p className="mt-2 text-body-sm font-medium text-content-primary">
              {alert.asset}
            </p>
          </div>
          <div className="space-y-2">
            <p className="type-label-sm">SOC metadata</p>
            <p className="type-mono-sm">source_ip: {alert.sourceIp}</p>
            <p className="type-mono-sm">destination_port: {alert.destinationPort ?? "n/a"}</p>
            <p className="type-mono-sm">timestamp: {alert.timestamp}</p>
            <p className="type-mono-sm">username: {alert.username}</p>
            <p className="type-mono-sm">event_id: {alert.eventId}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
