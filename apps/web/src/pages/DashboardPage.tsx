import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { ChartCard } from "../components/data-display/ChartCard";
import { DetectionScopeCallout } from "../components/data-display/DetectionScopeCallout";
import { MetricCard } from "../components/data-display/MetricCard";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard } from "../components/feedback/LoadingState";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Icon } from "../components/ui/Icon";
import { DistributionBars } from "../features/dashboard/components/DistributionBars";
import { LatestIncidentsPanel } from "../features/dashboard/components/LatestIncidentsPanel";
import { QuickLinksPanel } from "../features/dashboard/components/QuickLinksPanel";
import { RecentResponsesPanel } from "../features/dashboard/components/RecentResponsesPanel";
import { TopAffectedAssetsPanel } from "../features/dashboard/components/TopAffectedAssetsPanel";
import { useDashboardOverview } from "../features/dashboard/service";
import { formatTokenLabel } from "../lib/formatters";
import { pageBlueprints } from "../lib/theme/tokens";

const metricFormatter = new Intl.NumberFormat("en-US");
const tooltipContentStyle = {
  backgroundColor: "#111827",
  border: "1px solid #1F2937",
  borderRadius: "14px",
  boxShadow: "0 18px 40px rgba(0, 0, 0, 0.38)"
};
const tooltipLabelStyle = {
  color: "#D1D5DB",
  fontSize: "12px",
  letterSpacing: "0.12em",
  textTransform: "uppercase"
};
const tooltipItemStyle = {
  color: "#F9FAFB",
  fontSize: "12px",
  padding: 0
};

function formatCompactLabel(value: string) {
  return value.replace(/_/g, " ");
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { data, isLoading, error, reload } = useDashboardOverview();

  const summaryCards = useMemo(() => {
    if (!data) {
      return [];
    }

    return [
      {
        label: "Total alerts",
        value: metricFormatter.format(data.summary.totalAlerts),
        detail:
          "In-scope signals (Wazuh and Suricata) in the current window—your triage backlog.",
        tone: "highlight" as const,
        trend: <Badge tone="outline">{data.summary.pendingResponses} pending response</Badge>
      },
      {
        label: "High-risk alerts",
        value: metricFormatter.format(data.summary.highRiskAlerts),
        detail:
          "Risk score 70+ (brute force, FIM, port scan, or user creation)—review these first.",
        tone: "warning" as const,
        trend: <Badge tone="warning">avg risk {data.summary.averageRiskScore}</Badge>
      },
      {
        label: "Open incidents",
        value: metricFormatter.format(data.summary.openIncidents),
        detail:
          "Cases not yet resolved; drive each from triage through containment or closure.",
        tone: "danger" as const,
        trend: <Badge tone="outline">{data.latestIncidents.length} latest surfaced</Badge>
      },
      {
        label: "Active assets / endpoints",
        value: metricFormatter.format(data.summary.activeAssets),
        detail:
          "Monitored hosts online or degraded—cross-check with top affected assets below.",
        tone: "neutral" as const,
        trend: <Badge tone="outline">{data.topAffectedAssets.length} top in focus</Badge>
      },
      {
        label: "Recent responses",
        value: metricFormatter.format(data.summary.recentResponses),
        detail:
          "Policy actions in the last 24h (dry-run or live)—confirm what already ran.",
        tone: "neutral" as const,
        trend: <Badge tone="brand">{data.recentResponsesFeed.length} latest listed</Badge>
      }
    ];
  }, [data]);

  if (error && !data) {
    return (
      <ErrorState
        title="Dashboard summary could not be loaded"
        description="The overview depends on the backend summary and operational list endpoints, and the current request failed."
        details={error}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            Retry dashboard
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow={pageBlueprints.overview.eyebrow}
        title={pageBlueprints.overview.title}
        description={pageBlueprints.overview.description}
        meta={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="outline">four-detection scope</Badge>
            {data ? <Badge tone="brand">refreshed {data.fetchedAt}</Badge> : null}
          </div>
        }
        actions={
          <Button
            variant="secondary"
            size="sm"
            leadingIcon={<Icon name="activity" className="h-4 w-4" />}
            onClick={reload}
          >
            {isLoading && data ? "Refreshing" : "Refresh overview"}
          </Button>
        }
      />

      <DetectionScopeCallout />

      {error && data ? (
        <ErrorState
          title="Dashboard data is stale"
          description="The last successful overview is still visible, but a background refresh failed."
          details={error}
          action={
            <Button variant="secondary" size="sm" onClick={reload}>
              Retry refresh
            </Button>
          }
          tone="warning"
        />
      ) : null}

      {isLoading && !data ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </section>
          <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr_1fr]">
            <LoadingCard className="min-h-[22rem]" />
            <LoadingCard className="min-h-[22rem]" />
            <LoadingCard className="min-h-[22rem]" />
          </section>
          <section className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
            <LoadingCard className="min-h-[20rem]" />
            <LoadingCard className="min-h-[20rem]" />
          </section>
          <section className="grid gap-4 xl:grid-cols-2">
            <LoadingCard className="min-h-[20rem]" />
            <LoadingCard className="min-h-[20rem]" />
          </section>
        </>
      ) : data ? (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {summaryCards.map((card) => (
              <MetricCard
                key={card.label}
                label={card.label}
                value={card.value}
                detail={card.detail}
                tone={card.tone}
                trend={card.trend}
              />
            ))}
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr_1fr]">
            <ChartCard
              eyebrow="Alert volume over time"
              title="Live alert flow"
              description="What happened recently across the four supported scenarios—use the chips to see mix by detection."
              className="min-h-[23rem]"
              footer={
                <div className="flex flex-wrap items-center gap-2">
                  {data.alertsByDetection.map((item) => (
                    <Badge key={item.detectionType} tone="outline">
                      {formatTokenLabel(item.detectionType)}: {item.total}
                    </Badge>
                  ))}
                </div>
              }
            >
              <div className="surface-grid rounded-panel border border-border-subtle/80 p-4">
                {data.alertVolume.length ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart
                      data={data.alertVolume}
                      margin={{ top: 10, right: 8, left: -24, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient
                          id="aegiscoreDashboardVolume"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop offset="5%" stopColor="#F97316" stopOpacity={0.45} />
                          <stop offset="95%" stopColor="#F97316" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(156, 163, 175, 0.12)" vertical={false} />
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        allowDecimals={false}
                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={tooltipContentStyle}
                        labelStyle={tooltipLabelStyle}
                        itemStyle={tooltipItemStyle}
                      />
                      <Area
                        type="monotone"
                        dataKey="total"
                        stroke="#F97316"
                        strokeWidth={2.5}
                        fill="url(#aegiscoreDashboardVolume)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    iconName="alerts"
                    title="No alert volume for this window"
                    description="No timestamps in range yet, or ingestion is quiet. Refresh after new Wazuh or Suricata activity."
                  />
                )}
              </div>
            </ChartCard>

            <ChartCard
              eyebrow="Severity / risk"
              title="Priority distribution"
              description="How serious the queue looks: severity bands plus risk buckets (70+ is elevated)."
              className="min-h-[23rem]"
              actions={
                <Badge tone="warning">
                  avg risk {metricFormatter.format(data.summary.averageRiskScore)}
                </Badge>
              }
            >
              <div className="grid gap-4 lg:grid-cols-2">
                <DistributionBars title="Severity" items={data.severityDistribution} />
                <DistributionBars title="Risk buckets" items={data.riskDistribution} />
              </div>
            </ChartCard>

            <ChartCard
              eyebrow="Incident state"
              title="Investigation posture"
              description="Where open work sits in the lifecycle—new, triaged, investigating, contained, or resolved."
              className="min-h-[23rem]"
              actions={
                <Badge tone="outline">
                  {metricFormatter.format(data.summary.openIncidents)} open
                </Badge>
              }
            >
              <div className="surface-grid rounded-panel border border-border-subtle/80 p-4">
                {data.incidentStateDistribution.some((item) => item.total > 0) ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart
                      data={data.incidentStateDistribution}
                      layout="vertical"
                      margin={{ top: 8, right: 12, left: 6, bottom: 8 }}
                    >
                      <CartesianGrid stroke="rgba(156, 163, 175, 0.12)" horizontal={false} />
                      <XAxis
                        type="number"
                        allowDecimals={false}
                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        type="category"
                        dataKey="label"
                        tick={{ fill: "#D1D5DB", fontSize: 12 }}
                        tickLine={false}
                        axisLine={false}
                        width={92}
                        tickFormatter={formatCompactLabel}
                      />
                      <Tooltip
                        contentStyle={tooltipContentStyle}
                        labelStyle={tooltipLabelStyle}
                        itemStyle={tooltipItemStyle}
                        formatter={(value) => [value, "incidents"]}
                        labelFormatter={(value) => formatCompactLabel(String(value))}
                      />
                      <Bar dataKey="total" radius={[0, 8, 8, 0]}>
                        {data.incidentStateDistribution.map((item) => (
                          <Cell key={item.label} fill={item.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    iconName="incidents"
                    title="No incident state breakdown"
                    description="No incidents in the queue yet, or state counts are empty. Open the incidents queue when cases appear."
                  />
                )}
              </div>
            </ChartCard>
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
            <LatestIncidentsPanel
              incidents={data.latestIncidents}
              onOpenIncident={(incidentId) => navigate(`/incidents/${incidentId}`)}
              onViewQueue={() => navigate("/incidents")}
            />
            <QuickLinksPanel
              items={[
                {
                  id: "alerts",
                  label: "Alerts queue",
                  description: "Triage in-scope detections; sort by risk when the queue is full.",
                  value: metricFormatter.format(data.summary.highRiskAlerts),
                  icon: "alerts",
                  onClick: () => navigate("/alerts")
                },
                {
                  id: "incidents",
                  label: "Incidents queue",
                  description: "Group and close investigations tied to those alerts.",
                  value: metricFormatter.format(data.summary.openIncidents),
                  icon: "incidents",
                  onClick: () => navigate("/incidents")
                },
                {
                  id: "assets",
                  label: "Assets / endpoints",
                  description: "See which hosts carry the most alert load.",
                  value: metricFormatter.format(data.summary.activeAssets),
                  icon: "endpoints",
                  onClick: () => navigate("/assets")
                },
                {
                  id: "responses",
                  label: "Response history",
                  description: "Audit what policies already executed (dry-run or live).",
                  value: metricFormatter.format(data.summary.recentResponses),
                  icon: "responses",
                  onClick: () => navigate("/responses")
                }
              ]}
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <TopAffectedAssetsPanel
              assets={data.topAffectedAssets}
              onViewAssets={() => navigate("/assets")}
            />
            <RecentResponsesPanel
              responses={data.recentResponsesFeed}
              onViewResponses={() => navigate("/responses")}
            />
          </section>
        </>
      ) : (
        <EmptyState
          iconName="dashboard"
          title="Overview unavailable"
          description="Summary data did not load. Check the API and database, then retry."
          action={
            <Button variant="secondary" size="sm" onClick={reload}>
              Retry overview
            </Button>
          }
        />
      )}
    </div>
  );
}
