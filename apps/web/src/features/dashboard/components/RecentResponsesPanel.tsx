import { Button } from "../../../components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "../../../components/ui/Card";
import {
  ExecutionStatusBadge,
  ModeBadge
} from "../../responses/components/ResponseBadges";
import type { ResponseRecord } from "../../responses/types";
import { Badge } from "../../../components/ui/Badge";
import { formatTokenLabel } from "../../../lib/formatters";

type RecentResponsesPanelProps = {
  responses: ResponseRecord[];
  onViewResponses: () => void;
};

export function RecentResponsesPanel({
  responses,
  onViewResponses
}: RecentResponsesPanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="space-y-2">
          <p className="type-label-md">Most recent responses</p>
          <CardTitle>Execution history</CardTitle>
          <CardDescription>
            Wazuh/Suricata detect events; AI prioritizes alerts. Policy-driven actions and optional
            brute_force ML IP blocks appear here—see mode and outcome at a glance.
          </CardDescription>
        </div>
        <Button variant="ghost" size="sm" onClick={onViewResponses}>
          View responses
        </Button>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        {responses.length ? (
          responses.map((response) => (
            <div
              key={response.id}
              className="rounded-panel border border-border-subtle bg-surface-subtle/40 px-4 py-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="type-mono-sm">{response.id}</span>
                    <ModeBadge mode={response.mode} />
                    <ExecutionStatusBadge status={response.executionStatus} />
                    {response.policyName ? <Badge tone="brand">{response.policyName}</Badge> : null}
                  </div>
                  <div>
                    <h3 className="type-heading-sm">{formatTokenLabel(response.actionType)}</h3>
                    <p className="type-body-sm">{response.resultSummary}</p>
                    {response.resultMessage && response.resultMessage !== response.resultSummary ? (
                      <p className="type-body-sm text-content-muted">{response.resultMessage}</p>
                    ) : null}
                    {response.mlBruteBlockSummary ? (
                      <p className="type-body-sm text-content-secondary mt-2 rounded-panel border border-brand-primary/20 bg-surface-accentSoft/25 px-3 py-2">
                        {response.mlBruteBlockSummary}
                      </p>
                    ) : null}
                  </div>
                </div>
                <span className="type-mono-sm">{response.executedAt}</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
                <span className="type-body-sm">
                  Target: <span className="type-mono-sm">{response.target}</span>
                </span>
                <span className="type-body-sm">
                  Incident: <span className="type-mono-sm">{response.linkedEntity}</span>
                </span>
                <span className="type-body-sm">
                  Attempts: <span className="type-mono-sm">{response.attemptCount}</span>
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-panel border border-dashed border-border-subtle bg-surface-subtle/35 px-4 py-5">
            <p className="type-body-sm">
              No responses in this window. When policies fire, executions and outcomes
              will list here and on the response history page.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
