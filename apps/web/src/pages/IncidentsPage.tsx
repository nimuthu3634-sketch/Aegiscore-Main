import { useEffect, useState } from "react";
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
import { IncidentSummaryPanel } from "../features/incidents/components/IncidentSummaryPanel";
import { IncidentsTable } from "../features/incidents/components/IncidentsTable";
import { useIncidentsList } from "../features/incidents/service";
import type { IncidentRecord } from "../features/incidents/types";
import { pageBlueprints } from "../lib/theme/tokens";

export function IncidentsPage() {
  const { data, isLoading, error, reload } = useIncidentsList();
  const [query, setQuery] = useState("");
  const [priority, setPriority] = useState("");
  const [state, setState] = useState("");
  const [detectionType, setDetectionType] = useState("");
  const [assignee, setAssignee] = useState("");
  const [selectedIncidentId, setSelectedIncidentId] = useState("");

  const incidents = data?.items ?? [];

  const filteredIncidents = incidents.filter((incident) => {
    const normalizedQuery = query.trim().toLowerCase();
    const matchesQuery =
      !normalizedQuery ||
      [
        incident.id,
        incident.title,
        incident.primaryAsset,
        incident.assignee,
        incident.detectionType
      ].some((value) => value.toLowerCase().includes(normalizedQuery));

    const matchesPriority = !priority || incident.priority === priority;
    const matchesState = !state || incident.state === state;
    const matchesDetection = !detectionType || incident.detectionType === detectionType;
    const matchesAssignee = !assignee || incident.assignee === assignee;

    return (
      matchesQuery &&
      matchesPriority &&
      matchesState &&
      matchesDetection &&
      matchesAssignee
    );
  });

  useEffect(() => {
    if (!filteredIncidents.length) {
      setSelectedIncidentId("");
      return;
    }

    if (!filteredIncidents.some((incident) => incident.id === selectedIncidentId)) {
      setSelectedIncidentId(filteredIncidents[0].id);
    }
  }, [filteredIncidents, selectedIncidentId]);

  const selectedIncident =
    filteredIncidents.find((incident) => incident.id === selectedIncidentId) ??
    null;

  if (error) {
    return (
      <ErrorState
        title="Incidents could not be loaded"
        description="The queue structure is ready, but the current incident list request failed."
        details={error}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            Retry incidents
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow={pageBlueprints.incidents.eyebrow}
        title={pageBlueprints.incidents.title}
        description={pageBlueprints.incidents.description}
        meta={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand">{incidents.length} queue items</Badge>
            <Badge tone="outline">Split queue + summary layout</Badge>
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
              label="Open or triaged"
              value={String(
                filteredIncidents.filter(
                  (incident) =>
                    incident.state === "new" ||
                    incident.state === "triaged" ||
                    incident.state === "investigating"
                ).length
              )}
              detail="Analyst work remaining in the active queue."
              tone="highlight"
            />
            <MetricCard
              label="Critical or high"
              value={String(
                filteredIncidents.filter(
                  (incident) =>
                    incident.priority === "critical" ||
                    incident.priority === "high"
                ).length
              )}
              detail="Queue pressure that should remain visible at the top."
              tone="warning"
            />
            <MetricCard
              label="Assigned to queue"
              value={String(
                filteredIncidents.filter(
                  (incident) => incident.assignee === "SOC Queue"
                ).length
              )}
              detail="Incidents still waiting for named analyst ownership."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Incident queue filters"
        description="Keep the queue optimized for triage speed by filtering by priority, state, detection type, or analyst."
        search={<SearchInput value={query} onChange={(event) => setQuery(event.target.value)} />}
        filters={
          <>
            <Select
              aria-label="Filter incidents by priority"
              value={priority}
              onChange={(event) => setPriority(event.target.value)}
              placeholder="Priority"
              options={[
                { value: "critical", label: "Critical" },
                { value: "high", label: "High" },
                { value: "medium", label: "Medium" },
                { value: "low", label: "Low" }
              ]}
            />
            <Select
              aria-label="Filter incidents by state"
              value={state}
              onChange={(event) => setState(event.target.value)}
              placeholder="State"
              options={[
                { value: "new", label: "New" },
                { value: "triaged", label: "Triaged" },
                { value: "investigating", label: "Investigating" },
                { value: "contained", label: "Contained" },
                { value: "resolved", label: "Resolved" }
              ]}
            />
            <Select
              aria-label="Filter incidents by detection type"
              value={detectionType}
              onChange={(event) => setDetectionType(event.target.value)}
              placeholder="Detection"
              options={[...new Set(incidents.map((incident) => incident.detectionType))].map(
                (value) => ({ value, label: value })
              )}
            />
            <Select
              aria-label="Filter incidents by assignee"
              value={assignee}
              onChange={(event) => setAssignee(event.target.value)}
              placeholder="Assignee"
              options={[...new Set(incidents.map((incident) => incident.assignee))].map(
                (value) => ({ value, label: value })
              )}
            />
          </>
        }
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setQuery("");
              setPriority("");
              setState("");
              setDetectionType("");
              setAssignee("");
            }}
          >
            Reset filters
          </Button>
        }
        activeFilters={[
          priority && `priority:${priority}`,
          state && `state:${state}`,
          detectionType && `detection:${detectionType}`,
          assignee && `assignee:${assignee}`
        ].filter(Boolean) as string[]}
      />

      {isLoading ? (
        <LoadingTable columns={8} rows={5} />
      ) : filteredIncidents.length ? (
        <section className="grid gap-4 xl:grid-cols-[1.45fr_0.55fr]">
          <IncidentsTable
            incidents={filteredIncidents}
            selectedIncidentId={selectedIncidentId}
            onRowClick={(incident: IncidentRecord) =>
              setSelectedIncidentId(incident.id)
            }
          />
          <IncidentSummaryPanel incident={selectedIncident} />
        </section>
      ) : (
        <EmptyState
          iconName="incidents"
          title="No incidents match the current queue filters"
          description="Broaden the queue filters to restore the current incident set."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setQuery("");
                setPriority("");
                setState("");
                setDetectionType("");
                setAssignee("");
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
