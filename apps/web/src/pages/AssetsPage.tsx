import { useEffect, useMemo, useState } from "react";
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
import { AssetSummaryPanel } from "../features/assets/components/AssetSummaryPanel";
import { AssetsTable } from "../features/assets/components/AssetsTable";
import { useAssetsList } from "../features/assets/service";
import type { AssetEnvironment, AssetRecord, AssetsListQuery, AssetsSortField } from "../features/assets/types";
import { pageBlueprints } from "../lib/theme/tokens";

export function AssetsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<AssetsListQuery["status"]>("");
  const [criticality, setCriticality] = useState<AssetsListQuery["criticality"]>("");
  const [operatingSystem, setOperatingSystem] = useState("");
  const [environment, setEnvironment] = useState<AssetEnvironment | "">("");
  const [sortBy, setSortBy] = useState<AssetsSortField>("hostname");
  const [sortDirection, setSortDirection] = useState<AssetsListQuery["sortDirection"]>("asc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedAssetId, setSelectedAssetId] = useState("");

  const query = useMemo<AssetsListQuery>(
    () => ({
      search,
      status,
      criticality,
      operatingSystem,
      environment,
      sortBy,
      sortDirection,
      page,
      pageSize
    }),
    [
      criticality,
      environment,
      operatingSystem,
      page,
      pageSize,
      search,
      sortBy,
      sortDirection,
      status
    ]
  );

  const { data, isLoading, error, reload } = useAssetsList(query);
  const assets = useMemo(() => data?.items ?? [], [data?.items]);
  const meta = data?.meta;

  useEffect(() => {
    if (!assets.length) {
      setSelectedAssetId("");
      return;
    }

    if (!assets.some((asset) => asset.id === selectedAssetId)) {
      setSelectedAssetId(assets[0].id);
    }
  }, [assets, selectedAssetId]);

  const selectedAsset = assets.find((asset) => asset.id === selectedAssetId) ?? null;

  if (error) {
    return (
      <ErrorState
        title="Assets could not be loaded"
        description="The endpoint inventory page is using the backend query layer, but the current request failed."
        details={error}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            Retry assets
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow={pageBlueprints.assets.eyebrow}
        title={pageBlueprints.assets.title}
        description={pageBlueprints.assets.description}
        meta={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="outline">{data?.total ?? 0} monitored assets</Badge>
            <Badge tone="brand">
              {assets.filter((asset) => asset.openIncidents > 0).length} hosts with open incidents
            </Badge>
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
              label="Online agents"
              value={String(assets.filter((asset) => asset.agentStatus === "online").length)}
              detail="On this page: healthy telemetry from monitored hosts."
              tone="highlight"
            />
            <MetricCard
              label="Degraded or offline"
              value={String(assets.filter((asset) => asset.agentStatus !== "online").length)}
              detail="On this page: prioritize before trusting detections from these agents."
              tone="warning"
            />
            <MetricCard
              label="Recent alert pressure"
              value={String(
                assets.reduce((total, asset) => total + asset.recentAlertsCount, 0)
              )}
              detail="On this page: sum of in-scope alerts per visible host—pairs with top assets on the overview."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Asset inventory filters"
        description="Search by hostname, asset ID, or IP and reduce the inventory by status, criticality, OS, or environment."
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
              aria-label="Filter assets by agent status"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as AssetsListQuery["status"]);
                setPage(1);
              }}
              placeholder="Agent status"
              options={[
                { value: "online", label: "Online" },
                { value: "degraded", label: "Degraded" },
                { value: "offline", label: "Offline" }
              ]}
            />
            <Select
              aria-label="Filter assets by criticality"
              value={criticality}
              onChange={(event) => {
                setCriticality(event.target.value as AssetsListQuery["criticality"]);
                setPage(1);
              }}
              placeholder="Criticality"
              options={[
                { value: "mission_critical", label: "Mission critical" },
                { value: "high", label: "High" },
                { value: "standard", label: "Standard" },
                { value: "low", label: "Low" }
              ]}
            />
            <Select
              aria-label="Filter assets by operating system"
              value={operatingSystem}
              onChange={(event) => {
                setOperatingSystem(event.target.value);
                setPage(1);
              }}
              placeholder="Operating system"
              options={[...new Set(assets.map((asset) => asset.operatingSystem))].map(
                (value) => ({ value, label: value })
              )}
            />
            <Select
              aria-label="Filter assets by environment"
              value={environment}
              onChange={(event) => {
                setEnvironment(event.target.value as AssetEnvironment | "");
                setPage(1);
              }}
              placeholder="Environment"
              options={[
                { value: "production", label: "Production" },
                { value: "office", label: "Office" },
                { value: "remote", label: "Remote" }
              ]}
            />
          </>
        }
        actions={
          <>
            <Select
              aria-label="Sort assets by"
              value={sortBy}
              onChange={(event) => {
                setSortBy(event.target.value as AssetsSortField);
                setPage(1);
              }}
              options={[
                { value: "hostname", label: "Hostname" },
                { value: "last_seen", label: "Last seen" },
                { value: "recent_alerts", label: "Recent alerts" }
              ]}
            />
            <Select
              aria-label="Asset sort direction"
              value={sortDirection}
              onChange={(event) => {
                setSortDirection(event.target.value as AssetsListQuery["sortDirection"]);
                setPage(1);
              }}
              options={[
                { value: "asc", label: "Ascending" },
                { value: "desc", label: "Descending" }
              ]}
            />
            <Select
              aria-label="Assets page size"
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
                setStatus("");
                setCriticality("");
                setOperatingSystem("");
                setEnvironment("");
                setSortBy("hostname");
                setSortDirection("asc");
                setPage(1);
                setPageSize(10);
              }}
            >
              Reset filters
            </Button>
          </>
        }
        activeFilters={[
          status && `status:${status}`,
          criticality && `criticality:${criticality}`,
          operatingSystem && `os:${operatingSystem}`,
          environment && `environment:${environment}`,
          sortBy !== "hostname" && `sort:${sortBy}`,
          sortDirection !== "asc" && `dir:${sortDirection}`
        ].filter(Boolean) as string[]}
      />

      <QueryWarnings warnings={meta?.warnings ?? []} />

      {isLoading ? (
        <LoadingTable columns={7} rows={6} />
      ) : assets.length ? (
        <section className="grid gap-4 xl:grid-cols-[1.45fr_0.55fr]">
          <AssetsTable
            assets={assets}
            selectedAssetId={selectedAssetId}
            onRowClick={(asset: AssetRecord) => setSelectedAssetId(asset.id)}
            footer={
              meta ? (
                <TablePagination
                  page={meta.page}
                  pageSize={meta.pageSize}
                  total={meta.total}
                  totalPages={meta.totalPages}
                  itemLabel="assets"
                  onPageChange={setPage}
                />
              ) : null
            }
          />
          <AssetSummaryPanel asset={selectedAsset} />
        </section>
      ) : (
        <EmptyState
          iconName="endpoints"
          title="No assets match the current filters"
          description="Clear search and filters to see the full monitored inventory. Use this view alongside incidents for host-level context."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearch("");
                setStatus("");
                setCriticality("");
                setOperatingSystem("");
                setEnvironment("");
                setSortBy("hostname");
                setSortDirection("asc");
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
