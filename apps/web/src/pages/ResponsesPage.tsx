import { useMemo, useState } from "react";
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
import { ResponsesTable } from "../features/responses/components/ResponsesTable";
import { useResponsesList } from "../features/responses/service";
import type { ResponsesListQuery, ResponsesSortField } from "../features/responses/types";
import { formatTokenLabel } from "../lib/formatters";
import { pageBlueprints } from "../lib/theme/tokens";

const supportedActionTypes = [
  "block_ip",
  "disable_user",
  "quarantine_host_flag",
  "create_manual_review",
  "notify_admin"
];

export function ResponsesPage() {
  const [search, setSearch] = useState("");
  const [actionType, setActionType] = useState("");
  const [mode, setMode] = useState<ResponsesListQuery["mode"]>("");
  const [executionStatus, setExecutionStatus] = useState<ResponsesListQuery["executionStatus"]>("");
  const [sortBy, setSortBy] = useState<ResponsesSortField>("executed_at");
  const [sortDirection, setSortDirection] = useState<ResponsesListQuery["sortDirection"]>("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const query = useMemo<ResponsesListQuery>(
    () => ({
      search,
      actionType,
      mode,
      executionStatus,
      sortBy,
      sortDirection,
      page,
      pageSize
    }),
    [actionType, executionStatus, mode, page, pageSize, search, sortBy, sortDirection]
  );

  const { data, isLoading, error, reload } = useResponsesList(query);
  const responses = data?.items ?? [];
  const meta = data?.meta;

  if (error) {
    return (
      <ErrorState
        title="Response history could not be loaded"
        description="The response execution surface is using the backend query layer, but the current request failed."
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
            <Badge tone="outline">{data?.total ?? 0} execution records</Badge>
            <Badge tone="brand">auditable executions</Badge>
          </div>
        }
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          <>
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </>
        ) : (
          <>
            <MetricCard
              label="Policy-backed"
              value={String(
                responses.filter((response) => Boolean(response.policyName)).length
              )}
              detail="Current page slice of backend policy-driven executions with named policy context."
              tone="highlight"
            />
            <MetricCard
              label="Live mode"
              value={String(
                responses.filter((response) => response.mode === "live").length
              )}
              detail="Current page slice of live actions or live workflow records."
            />
            <MetricCard
              label="Warnings or failures"
              value={String(
                responses.filter(
                  (response) =>
                    response.executionStatus === "warning" ||
                    response.executionStatus === "failed"
                ).length
              )} 
              detail="Current page slice needing analyst review before policy promotion."
              tone="warning"
            />
            <MetricCard
              label="Pending"
              value={String(
                responses.filter((response) => response.executionStatus === "pending").length
              )}
              detail="Current page slice of queued or in-progress response actions."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Response execution filters"
        description="Filter executions from policies across validated detections. Built-in ML IP blocks appear only for brute_force (TensorFlow High + login-density gates); other types use policies only."
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
              aria-label="Filter responses by action type"
              value={actionType}
              onChange={(event) => {
                setActionType(event.target.value);
                setPage(1);
              }}
              placeholder="Action type"
              options={[...new Set([...supportedActionTypes, ...responses.map((response) => response.actionType)])]
                .sort((left, right) => left.localeCompare(right))
                .map((value) => ({ value, label: formatTokenLabel(value) }))}
            />
            <Select
              aria-label="Filter responses by mode"
              value={mode}
              onChange={(event) => {
                setMode(event.target.value as ResponsesListQuery["mode"]);
                setPage(1);
              }}
              placeholder="Mode"
              options={[
                { value: "dry-run", label: "Dry-run" },
                { value: "live", label: "Live" }
              ]}
            />
            <Select
              aria-label="Filter responses by execution status"
              value={executionStatus}
              onChange={(event) => {
                setExecutionStatus(
                  event.target.value as ResponsesListQuery["executionStatus"]
                );
                setPage(1);
              }}
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
          <>
            <Select
              aria-label="Sort responses by"
              value={sortBy}
              onChange={(event) => {
                setSortBy(event.target.value as ResponsesSortField);
                setPage(1);
              }}
              options={[
                { value: "executed_at", label: "Executed at" },
                { value: "status", label: "Status" }
              ]}
            />
            <Select
              aria-label="Response sort direction"
              value={sortDirection}
              onChange={(event) => {
                setSortDirection(event.target.value as ResponsesListQuery["sortDirection"]);
                setPage(1);
              }}
              options={[
                { value: "desc", label: "Descending" },
                { value: "asc", label: "Ascending" }
              ]}
            />
            <Select
              aria-label="Responses page size"
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
                setActionType("");
                setMode("");
                setExecutionStatus("");
                setSortBy("executed_at");
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
          actionType && `action:${actionType}`,
          mode && `mode:${mode}`,
          executionStatus && `status:${executionStatus}`,
          sortBy !== "executed_at" && `sort:${sortBy}`,
          sortDirection !== "desc" && `dir:${sortDirection}`
        ].filter(Boolean) as string[]}
      />

      <QueryWarnings warnings={meta?.warnings ?? []} />

      {isLoading ? (
        <LoadingTable columns={8} rows={6} />
      ) : responses.length ? (
        <ResponsesTable
          responses={responses}
          footer={
            meta ? (
              <TablePagination
                page={meta.page}
                pageSize={meta.pageSize}
                total={meta.total}
                totalPages={meta.totalPages}
                itemLabel="responses"
                onPageChange={setPage}
              />
            ) : null
          }
        />
      ) : (
        <EmptyState
          iconName="responses"
          title="No response executions match the current filters"
          description="Clear filters to see the full audit trail. Nothing here usually means policies have not fired in this view yet."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearch("");
                setActionType("");
                setMode("");
                setExecutionStatus("");
                setSortBy("executed_at");
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
