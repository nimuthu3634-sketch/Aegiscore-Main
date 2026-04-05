import { Button } from "../../../components/ui/Button";
import { IncidentStateBadge } from "../../../components/ui/IncidentStateBadge";
import { PriorityChip } from "../../../components/ui/PriorityChip";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../../../components/ui/Card";
import type { IncidentRecord } from "../../incidents/types";

type LatestIncidentsPanelProps = {
  incidents: IncidentRecord[];
  onOpenIncident: (incidentId: string) => void;
  onViewQueue: () => void;
};

export function LatestIncidentsPanel({
  incidents,
  onOpenIncident,
  onViewQueue
}: LatestIncidentsPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="space-y-2">
          <p className="type-label-md">Latest incidents</p>
          <CardTitle>Investigation queue</CardTitle>
          <CardDescription>
            Recently updated investigations with enough context to jump straight into
            triage.
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={onViewQueue}>
          View queue
        </Button>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        {incidents.length ? (
          incidents.map((incident) => (
            <button
              key={incident.id}
              type="button"
              onClick={() => onOpenIncident(incident.id)}
              className="focus-ring w-full rounded-panel border border-border-subtle bg-surface-subtle/40 px-4 py-3 text-left transition hover:border-brand-primary/30 hover:bg-surface-subtle/70"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="type-mono-sm">{incident.id}</span>
                    <PriorityChip priority={incident.priority} />
                    <IncidentStateBadge state={incident.state} />
                  </div>
                  <div>
                    <h3 className="type-heading-sm">{incident.title}</h3>
                    <p className="type-body-sm">{incident.summary}</p>
                  </div>
                </div>
                <span className="type-mono-sm">{incident.lastUpdated}</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
                <span className="type-body-sm">
                  Asset: <span className="type-mono-sm">{incident.primaryAsset}</span>
                </span>
                <span className="type-body-sm">
                  Alerts: <span className="type-mono-sm">{incident.linkedAlertsCount}</span>
                </span>
                <span className="type-body-sm">
                  Assignee: <span className="type-mono-sm">{incident.assignee}</span>
                </span>
              </div>
            </button>
          ))
        ) : (
          <div className="rounded-panel border border-dashed border-border-subtle bg-surface-subtle/35 px-4 py-5">
            <p className="type-body-sm">
              No incidents are available in the current backend dataset.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
