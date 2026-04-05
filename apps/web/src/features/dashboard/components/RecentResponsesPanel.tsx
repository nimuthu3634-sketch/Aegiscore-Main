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
            The latest automated or analyst-triggered response actions returned by the
            backend.
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
                  </div>
                  <div>
                    <h3 className="type-heading-sm">{response.actionType}</h3>
                    <p className="type-body-sm">{response.resultSummary}</p>
                  </div>
                </div>
                <span className="type-mono-sm">{response.executedAt}</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
                <span className="type-body-sm">
                  Target: <span className="type-mono-sm">{response.target}</span>
                </span>
                <span className="type-body-sm">
                  Linked entity: <span className="type-mono-sm">{response.linkedEntity}</span>
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-panel border border-dashed border-border-subtle bg-surface-subtle/35 px-4 py-5">
            <p className="type-body-sm">
              No response executions are available in the current history window.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
