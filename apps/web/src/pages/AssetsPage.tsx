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
import { AssetSummaryPanel } from "../features/assets/components/AssetSummaryPanel";
import { AssetsTable } from "../features/assets/components/AssetsTable";
import { useAssetsList } from "../features/assets/service";
import type { AssetRecord } from "../features/assets/types";
import { pageBlueprints } from "../lib/theme/tokens";

export function AssetsPage() {
  const { data, isLoading, error, reload } = useAssetsList();
  const [query, setQuery] = useState("");
  const [agentStatus, setAgentStatus] = useState("");
  const [criticality, setCriticality] = useState("");
  const [operatingSystem, setOperatingSystem] = useState("");
  const [environment, setEnvironment] = useState("");
  const [selectedAssetId, setSelectedAssetId] = useState("");

  const assets = data?.items ?? [];

  const filteredAssets = assets.filter((asset) => {
    const normalizedQuery = query.trim().toLowerCase();
    const matchesQuery =
      !normalizedQuery ||
      [
        asset.hostname,
        asset.id,
        asset.ipAddress,
        asset.operatingSystem,
        asset.environment
      ].some((value) => value.toLowerCase().includes(normalizedQuery));

    const matchesStatus = !agentStatus || asset.agentStatus === agentStatus;
    const matchesCriticality = !criticality || asset.criticality === criticality;
    const matchesOs = !operatingSystem || asset.operatingSystem === operatingSystem;
    const matchesEnvironment = !environment || asset.environment === environment;

    return (
      matchesQuery &&
      matchesStatus &&
      matchesCriticality &&
      matchesOs &&
      matchesEnvironment
    );
  });

  useEffect(() => {
    if (!filteredAssets.length) {
      setSelectedAssetId("");
      return;
    }

    if (!filteredAssets.some((asset) => asset.id === selectedAssetId)) {
      setSelectedAssetId(filteredAssets[0].id);
    }
  }, [filteredAssets, selectedAssetId]);

  const selectedAsset =
    filteredAssets.find((asset) => asset.id === selectedAssetId) ?? null;

  if (error) {
    return (
      <ErrorState
        title="Assets could not be loaded"
        description="The endpoint inventory page is ready, but the current asset dataset request failed."
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
            <Badge tone="outline">{assets.length} monitored assets</Badge>
            <Badge tone="brand">
              {assets.filter((asset) => asset.openIncidents > 0).length} with incidents
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
              value={String(
                filteredAssets.filter((asset) => asset.agentStatus === "online").length
              )}
              detail="Endpoints reporting healthy telemetry into the current tenant."
              tone="highlight"
            />
            <MetricCard
              label="Degraded or offline"
              value={String(
                filteredAssets.filter((asset) => asset.agentStatus !== "online").length
              )}
              detail="Operational assets that may need endpoint or agent attention."
              tone="warning"
            />
            <MetricCard
              label="Recent alert pressure"
              value={String(
                filteredAssets.reduce(
                  (total, asset) => total + asset.recentAlertsCount,
                  0
                )
              )}
              detail="Total recent alerts across the currently visible assets."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Asset inventory filters"
        description="Search by hostname, asset ID, or IP and reduce the inventory by status, criticality, OS, or environment."
        search={<SearchInput value={query} onChange={(event) => setQuery(event.target.value)} />}
        filters={
          <>
            <Select
              aria-label="Filter assets by agent status"
              value={agentStatus}
              onChange={(event) => setAgentStatus(event.target.value)}
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
              onChange={(event) => setCriticality(event.target.value)}
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
              onChange={(event) => setOperatingSystem(event.target.value)}
              placeholder="Operating system"
              options={[...new Set(assets.map((asset) => asset.operatingSystem))].map(
                (value) => ({ value, label: value })
              )}
            />
            <Select
              aria-label="Filter assets by environment"
              value={environment}
              onChange={(event) => setEnvironment(event.target.value)}
              placeholder="Environment"
              options={[...new Set(assets.map((asset) => asset.environment))].map(
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
              setAgentStatus("");
              setCriticality("");
              setOperatingSystem("");
              setEnvironment("");
            }}
          >
            Reset filters
          </Button>
        }
        activeFilters={[
          agentStatus && `status:${agentStatus}`,
          criticality && `criticality:${criticality}`,
          operatingSystem && `os:${operatingSystem}`,
          environment && `environment:${environment}`
        ].filter(Boolean) as string[]}
      />

      {isLoading ? (
        <LoadingTable columns={7} rows={6} />
      ) : filteredAssets.length ? (
        <section className="grid gap-4 xl:grid-cols-[1.45fr_0.55fr]">
          <AssetsTable
            assets={filteredAssets}
            selectedAssetId={selectedAssetId}
            onRowClick={(asset: AssetRecord) => setSelectedAssetId(asset.id)}
          />
          <AssetSummaryPanel asset={selectedAsset} />
        </section>
      ) : (
        <EmptyState
          iconName="endpoints"
          title="No assets match the current filters"
          description="Broaden the asset filters or clear the search to restore the operational endpoint list."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setQuery("");
                setAgentStatus("");
                setCriticality("");
                setOperatingSystem("");
                setEnvironment("");
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
