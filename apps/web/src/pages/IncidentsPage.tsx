import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MetricCard } from "../components/data-display/MetricCard";
import { SearchFilterToolbar } from "../components/data-display/SearchFilterToolbar";
import { TablePagination } from "../components/data-display/TablePagination";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { QueryWarnings } from "../components/feedback/QueryWarnings";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { IncidentsTable } from "../features/incidents/components/IncidentsTable";
import { useIncidentsList } from "../features/incidents/service";
import type { IncidentStateFilter, IncidentsListQuery, IncidentsSortField } from "../features/incidents/types";
import { supportedDetectionSelectOptions } from "../lib/supportedDetections";
import { pageBlueprints } from "../lib/theme/tokens";

export function IncidentsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [priority, setPriority] = useState<IncidentsListQuery["priority"]>("");
  const [state, setState] = useState<IncidentStateFilter | "">("");
  const [detectionType, setDetectionType] = useState("");
  const [assignee, setAssignee] = useState("");
  const [sortBy, setSortBy] = useState<IncidentsSortField>("updated_at");
  const [sortDirection, setSortDirection] = useState<IncidentsListQuery["sortDirection"]>("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const query = useMemo<IncidentsListQuery>(
    () => ({
      search,
      priority,
      state,
      detectionType,
      assignee,
      sortBy,
      sortDirection,
      page,
      pageSize
    }),
    [assignee, detectionType, page, pageSize, priority, search, sortBy, sortDirection, state]
  );

  const { data, isLoading, error, reload } = useIncidentsList(query);
  const incidents = data?.items ?? [];
  const meta = data?.meta;

  if (error) {
    return (
      <ErrorState
        title="Incidents could not be loaded"
        description="The investigation queue is using the backend query layer, but the current request failed."
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
            <Badge tone="brand">{data?.total ?? 0} queue items</Badge>
            <Badge tone="outline">Server-backed queue controls</Badge>
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
              value={String(meta?.total ?? 0)}
              detail="Total incidents matching the current server-side queue filters."
              tone="highlight"
            />
            <MetricCard
              label="Critical or high"
              value={String(
                incidents.filter(
                  (incident) =>
                    incident.priority === "critical" || incident.priority === "high"
                ).length
              )}
              detail="Current page slice of the highest-pressure investigation work."
              tone="warning"
            />
            <MetricCard
              label="Assigned to queue"
              value={String(
                incidents.filter((incident) => incident.assignee === "SOC Queue").length
              )}
              detail="Current page slice still waiting for named analyst ownership."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Incident queue filters"
        description="Keep the queue optimized for triage speed by filtering by priority, state, detection type, or analyst."
        search={
          <SearchInput
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        }
        filters={
          <>
            <Select
              aria-label="Filter incidents by priority"
              value={priority}
              onChange={(event) => {
                setPriority(event.target.value as IncidentsListQuery["priority"]);
                setPage(1);
              }}
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
              onChange={(event) => {
                setState(event.target.value as IncidentStateFilter | "");
                setPage(1);
              }}
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
              onChange={(event) => {
                setDetectionType(event.target.value);
                setPage(1);
              }}
              placeholder="Detection"
              options={supportedDetectionSelectOptions()}
            />
            <Select
              aria-label="Filter incidents by assignee"
              value={assignee}
              onChange={(event) => {
                setAssignee(event.target.value);
                setPage(1);
              }}
              placeholder="Assignee"
              options={[...new Set(incidents.map((incident) => incident.assignee))].map(
                (value) => ({ value, label: value })
              )}
            />
          </>
        }
        actions={
          <>
            <Select
              aria-label="Sort incidents by"
              value={sortBy}
              onChange={(event) => {
                setSortBy(event.target.value as IncidentsSortField);
                setPage(1);
              }}
              options={[
                { value: "updated_at", label: "Last updated" },
                { value: "created_at", label: "Created at" },
                { value: "priority", label: "Priority" }
              ]}
            />
            <Select
              aria-label="Incident sort direction"
              value={sortDirection}
              onChange={(event) => {
                setSortDirection(event.target.value as IncidentsListQuery["sortDirection"]);
                setPage(1);
              }}
              options={[
                { value: "desc", label: "Descending" },
                { value: "asc", label: "Ascending" }
              ]}
            />
            <Select
              aria-label="Incidents page size"
              value={String(pageSize)}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(1);
              }}
              options={[
                { value: "10", label: "10 / page" },
                { value: "25", label: "25 / page" },
                { value: "50", label: "50 / page" }
              ]}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearch("");
                setPriority("");
                setState("");
                setDetectionType("");
                setAssignee("");
                setSortBy("updated_at");
                setSortDirection("desc");
                setPage(1);
                setPageSize(10);
              }}
            >
              Reset filters
            </Button>
          </>
        }
        activeFilters={[
          priority && `priority:${priority}`,
          state && `state:${state}`,
          detectionType && `detection:${detectionType}`,
          assignee && `assignee:${assignee}`,
          sortBy !== "updated_at" && `sort:${sortBy}`,
          sortDirection !== "desc" && `dir:${sortDirection}`
        ].filter(Boolean) as string[]}
      />

      <QueryWarnings warnings={meta?.warnings ?? []} />

      {isLoading ? (
        <LoadingTable columns={8} rows={5} />
      ) : incidents.length ? (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="type-body-sm">
              Select a queue row to open the full incident investigation workspace.
            </p>
            <Badge tone="outline">detail route enabled</Badge>
          </div>
          <IncidentsTable
            incidents={incidents}
            onRowClick={(incident) => navigate(`/incidents/${incident.id}`)}
            footer={
              meta ? (
                <TablePagination
                  page={meta.page}
                  pageSize={meta.pageSize}
                  total={meta.total}
                  totalPages={meta.totalPages}
                  itemLabel="incidents"
                  onPageChange={setPage}
                />
              ) : null
            }
          />
        </section>
      ) : (
        <EmptyState
          iconName="incidents"
          title="No incidents match the current queue filters"
          description="Broaden the server-side queue filters to restore the current incident set."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearch("");
                setPriority("");
                setState("");
                setDetectionType("");
                setAssignee("");
                setSortBy("updated_at");
                setSortDirection("desc");
                setPage(1);
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
