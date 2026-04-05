import { useNavigate, useParams } from "react-router-dom";
import { AnalystNotesPanel } from "../components/data-display/AnalystNotesPanel";
import { DetailHeader } from "../components/data-display/DetailHeader";
import { EvidencePanel } from "../components/data-display/EvidencePanel";
import { KeyValueGrid, type KeyValueItem } from "../components/data-display/KeyValueGrid";
import { RawPayloadViewer } from "../components/data-display/RawPayloadViewer";
import { RelatedResponsesPanel } from "../components/data-display/RelatedResponsesPanel";
import { ScoreExplanationCard } from "../components/data-display/ScoreExplanationCard";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SeverityChip } from "../components/ui/SeverityChip";
import { StatusChip } from "../components/ui/StatusChip";
import { useAlertDetail } from "../features/alerts/detail/service";

function fallbackValue(value: string | null | undefined) {
  return value ?? "n/a";
}

export function AlertDetailPage() {
  const navigate = useNavigate();
  const { alertId } = useParams<{ alertId: string }>();
  const { data, isLoading, error, notFound, reload } = useAlertDetail(alertId);

  if (isLoading) {
    return (
      <div className="space-y-section">
        <LoadingCard className="min-h-[220px]" />
        <section className="grid gap-4 2xl:grid-cols-[1.35fr_0.65fr]">
          <div className="space-y-4">
            <LoadingCard className="min-h-[240px]" />
            <LoadingCard className="min-h-[280px]" />
          </div>
          <div className="space-y-4">
            <LoadingCard className="min-h-[220px]" />
            <LoadingCard className="min-h-[220px]" />
          </div>
        </section>
        <LoadingTable columns={6} rows={4} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-section">
        <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
          Back to alerts
        </Button>
        <ErrorState
          title="Alert detail could not be loaded"
          description="The investigation detail surface is ready, but the current alert detail request failed."
          details={error}
          action={
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" size="sm" onClick={reload}>
                Retry detail
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
                Return to queue
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  if (notFound || !data) {
    return (
      <div className="space-y-section">
        <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
          Back to alerts
        </Button>
        <EmptyState
          iconName="alerts"
          title="Alert record was not found"
          description="The requested alert is not available in the current dataset. Return to the queue and select another alert."
          action={
            <Button variant="secondary" size="sm" onClick={() => navigate("/alerts")}>
              Open alerts queue
            </Button>
          }
        />
      </div>
    );
  }

  const { alert, fetchedAt } = data;

  const metadataItems: KeyValueItem[] = [
    { label: "Alert ID", value: alert.id, mono: true, emphasized: true },
    { label: "Source IP", value: fallbackValue(alert.sourceIp), mono: true },
    { label: "Destination IP", value: fallbackValue(alert.destinationIp), mono: true },
    {
      label: "Destination port",
      value: fallbackValue(alert.destinationPort),
      mono: true
    },
    { label: "Asset / hostname", value: fallbackValue(alert.asset), emphasized: true },
    { label: "Username", value: fallbackValue(alert.username), mono: true },
    { label: "Timestamp", value: alert.timestamp, mono: true },
    {
      label: "Rule ID / source rule",
      value: [alert.ruleId, alert.sourceRule].filter(Boolean).join(" / ") || "n/a",
      mono: true
    }
  ];

  return (
    <div className="space-y-section">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
          Back to alerts
        </Button>
        <Badge tone="outline">fetched {fetchedAt}</Badge>
      </div>

      <DetailHeader
        eyebrow="Alert investigation"
        title={alert.detectionType}
        description={alert.normalizedSummary}
        badges={
          <>
            <Badge tone="outline">{alert.id}</Badge>
            <Badge tone="outline">{alert.sourceType}</Badge>
            <SeverityChip severity={alert.severity} />
            <StatusChip status={alert.status} />
            <Badge tone="brand">risk {alert.riskScore ?? "n/a"}</Badge>
            {alert.linkedIncidentId ? (
              <Badge tone="outline">incident {alert.linkedIncidentId}</Badge>
            ) : (
              <Badge tone="neutral">no linked incident</Badge>
            )}
          </>
        }
        actions={
          <div className="flex flex-wrap gap-3">
            {alert.linkedIncidentId ? (
              <Button
                size="sm"
                onClick={() => navigate(`/incidents/${alert.linkedIncidentId}`)}
              >
                Open linked incident
              </Button>
            ) : null}
            <Button variant="secondary" size="sm">
              Export evidence placeholder
            </Button>
          </div>
        }
      >
        <KeyValueGrid items={metadataItems} columns={4} />
      </DetailHeader>

      <section className="grid gap-4 2xl:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-4">
          <EvidencePanel
            eyebrow="Common schema"
            title="Normalized details"
            description="AegisCore-normalized evidence aligned to the future backend detail response."
          >
            <KeyValueGrid items={alert.normalizedDetails} columns={3} />
          </EvidencePanel>

          <RawPayloadViewer payload={alert.rawPayload} />

          <RelatedResponsesPanel responses={alert.relatedResponses} />

          <AnalystNotesPanel
            notes={alert.notes}
            composerLabel="Add alert investigation note"
          />
        </div>

        <div className="space-y-4">
          {alert.scoreExplanation ? (
            <ScoreExplanationCard
              label={alert.scoreExplanation.label}
              summary={alert.scoreExplanation.summary}
              rationale={alert.scoreExplanation.rationale}
              scoreValue={
                <span className="type-mono-sm">
                  {alert.scoreExplanation.score ?? "n/a"}
                </span>
              }
              factors={alert.scoreExplanation.factors}
            />
          ) : (
            <EvidencePanel
              eyebrow="Scoring"
              title="Score explanation unavailable"
              description="The backend did not return a risk explanation for this alert yet."
            >
              <p className="type-body-sm">
                The detail flow remains connected to the backend, but this alert does not currently include a score rationale payload.
              </p>
            </EvidencePanel>
          )}

          <EvidencePanel
            eyebrow="Workflow"
            title="Lifecycle actions"
            description="Action controls are structured here so backend mutation endpoints can plug in next."
          >
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <Button variant="secondary" size="sm">
                  Acknowledge
                </Button>
                <Button variant="secondary" size="sm">
                  Link to incident
                </Button>
                <Button variant="ghost" size="sm">
                  Close
                </Button>
              </div>
              <p className="type-body-sm">
                These placeholder controls mark the exact action area for upcoming analyst workflow APIs.
              </p>
            </div>
          </EvidencePanel>

          <EvidencePanel
            eyebrow="Context"
            title="Incident linkage"
            description="Incident relationship status for this alert."
          >
            {alert.linkedIncidentId ? (
              <div className="space-y-3">
                <p className="type-body-sm">
                  This alert is already linked into the broader incident investigation below.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <Badge tone="brand">{alert.linkedIncidentId}</Badge>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/incidents/${alert.linkedIncidentId}`)}
                  >
                    Open incident detail
                  </Button>
                </div>
              </div>
            ) : (
              <div className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4">
                <p className="type-body-sm">
                  No incident linkage exists yet. The link action placeholder above is ready for future correlation workflows.
                </p>
              </div>
            )}
          </EvidencePanel>
        </div>
      </section>
    </div>
  );
}
