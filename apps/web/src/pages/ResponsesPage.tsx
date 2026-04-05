import { MetricCard } from "../components/data-display/MetricCard";
import { SearchFilterToolbar } from "../components/data-display/SearchFilterToolbar";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { ResponsesTable } from "../features/responses/components/ResponsesTable";
import { useResponsesList } from "../features/responses/service";
import { pageBlueprints } from "../lib/theme/tokens";
import { useState } from "react";

export function ResponsesPage() {
  const { data, isLoading, error, reload } = useResponsesList();
  const [query, setQuery] = useState("");
  const [actionType, setActionType] = useState("");
  const [mode, setMode] = useState("");
  const [executionStatus, setExecutionStatus] = useState("");

  const responses = data?.items ?? [];

  const filteredResponses = responses.filter((response) => {
    const normalizedQuery = query.trim().toLowerCase();
    const matchesQuery =
      !normalizedQuery ||
      [
        response.id,
        response.actionType,
        response.target,
        response.linkedEntity,
        response.resultSummary
      ].some((value) => value.toLowerCase().includes(normalizedQuery));

    const matchesAction = !actionType || response.actionType === actionType;
    const matchesMode = !mode || response.mode === mode;
    const matchesExecution =
      !executionStatus || response.executionStatus === executionStatus;

    return matchesQuery && matchesAction && matchesMode && matchesExecution;
  });

  if (error) {
    return (
      <ErrorState
        title="Response history could not be loaded"
        description="The response execution surface is ready, but the current response dataset request failed."
        details={error}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            Retry responses
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow={pageBlueprints.responses.eyebrow}
        title={pageBlueprints.responses.title}
        description={pageBlueprints.responses.description}
        meta={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="outline">{responses.length} execution records</Badge>
            <Badge tone="brand">Dry-run and live actions</Badge>
          </div>
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        {isLoading ? (
          <>
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </>
        ) : (
          <>
            <MetricCard
              label="Succeeded"
              value={String(
                filteredResponses.filter(
                  (response) => response.executionStatus === "succeeded"
                ).length
              )}
              detail="Completed actions with clear auditable outcomes."
              tone="highlight"
            />
            <MetricCard
              label="Warnings or failures"
              value={String(
                filteredResponses.filter(
                  (response) =>
                    response.executionStatus === "warning" ||
                    response.executionStatus === "failed"
                ).length
              )}
              detail="Actions that need analyst review before policy promotion."
              tone="warning"
            />
            <MetricCard
              label="Pending"
              value={String(
                filteredResponses.filter(
                  (response) => response.executionStatus === "pending"
                ).length
              )}
              detail="Queued or approval-bound response actions."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Response execution filters"
        description="Compact analyst-friendly filtering for action type, run mode, and execution outcome."
        search={<SearchInput value={query} onChange={(event) => setQuery(event.target.value)} />}
        filters={
          <>
            <Select
              aria-label="Filter responses by action type"
              value={actionType}
              onChange={(event) => setActionType(event.target.value)}
              placeholder="Action type"
              options={[...new Set(responses.map((response) => response.actionType))].map(
                (value) => ({ value, label: value })
              )}
            />
            <Select
              aria-label="Filter responses by mode"
              value={mode}
              onChange={(event) => setMode(event.target.value)}
              placeholder="Mode"
              options={[
                { value: "dry-run", label: "Dry-run" },
                { value: "live", label: "Live" }
              ]}
            />
            <Select
              aria-label="Filter responses by execution status"
              value={executionStatus}
              onChange={(event) => setExecutionStatus(event.target.value)}
              placeholder="Execution status"
              options={[
                { value: "succeeded", label: "Succeeded" },
                { value: "warning", label: "Warning" },
                { value: "failed", label: "Failed" },
                { value: "pending", label: "Pending" }
              ]}
            />
          </>
        }
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setQuery("");
              setActionType("");
              setMode("");
              setExecutionStatus("");
            }}
          >
            Reset filters
          </Button>
        }
        activeFilters={[
          actionType && `action:${actionType}`,
          mode && `mode:${mode}`,
          executionStatus && `status:${executionStatus}`
        ].filter(Boolean) as string[]}
      />

      {isLoading ? (
        <LoadingTable columns={8} rows={6} />
      ) : filteredResponses.length ? (
        <ResponsesTable responses={filteredResponses} />
      ) : (
        <EmptyState
          iconName="responses"
          title="No response executions match the current filters"
          description="Clear the response filters to restore the current action history."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setQuery("");
                setActionType("");
                setMode("");
                setExecutionStatus("");
              }}
            >
              Clear filters
            </Button>
          }
        />
      )}
    </div>
  );
}
