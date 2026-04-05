import { useCallback } from "react";
import { fetchApiJson, formatUtcDateTime } from "../../lib/api";
import { buildApiPath } from "../../lib/api/query";
import { mapAlertsListResponse, mapAssetsListResponse, mapIncidentsListResponse, mapResponsesListResponse } from "../../lib/api/listTransforms";
import { useAsyncResource } from "../../lib/data/useAsyncResource";
import type { AlertsListApiResponse } from "../alerts/types";
import type { AssetsListApiResponse } from "../assets/types";
import type { IncidentsListApiResponse } from "../incidents/types";
import type { ResponsesListApiResponse } from "../responses/types";
import type {
  DashboardDetectionPoint,
  DashboardDistributionPoint,
  DashboardOverviewResponse,
  DashboardSummaryApiResponse,
  DashboardTrendPoint
} from "./types";

const severityPalette = {
  critical: "#EF4444",
  high: "#F97316",
  medium: "#F59E0B",
  low: "#9CA3AF"
} as const;

const incidentStatePalette = {
  new: "#9CA3AF",
  triaged: "#F59E0B",
  investigating: "#F97316",
  contained: "#22C55E",
  resolved: "#22C55E",
  false_positive: "#9CA3AF"
} as const;

const riskPalette = {
  "80+": "#F97316",
  "60-79": "#F59E0B",
  "<60": "#9CA3AF"
} as const;

type SeverityBucket = keyof typeof severityPalette;
type IncidentStateBucket = keyof typeof incidentStatePalette;

function formatShortTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
}

function buildAlertVolume(createdAtValues: string[]): DashboardTrendPoint[] {
  const totals = new Map<string, number>();
  const bucketByHour = createdAtValues.length > 12;

  createdAtValues.forEach((value) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return;
    }

    const label = bucketByHour
      ? `${String(date.getUTCHours()).padStart(2, "0")}:00`
      : formatShortTime(value);

    totals.set(label, (totals.get(label) ?? 0) + 1);
  });

  return [...totals.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([label, total]) => ({ label, total }));
}

function buildSeverityDistribution(
  severities: Array<"critical" | "high" | "medium" | "low">
): DashboardDistributionPoint[] {
  const orderedBuckets: SeverityBucket[] = ["critical", "high", "medium", "low"];

  return orderedBuckets.map((label) => ({
    label,
    total: severities.filter((severity) => severity === label).length,
    color: severityPalette[label]
  }));
}

function buildRiskDistribution(riskScores: Array<number | null>): DashboardDistributionPoint[] {
  const buckets = {
    "80+": 0,
    "60-79": 0,
    "<60": 0
  };

  riskScores.forEach((score) => {
    if ((score ?? 0) >= 80) {
      buckets["80+"] += 1;
    } else if ((score ?? 0) >= 60) {
      buckets["60-79"] += 1;
    } else {
      buckets["<60"] += 1;
    }
  });

  return (Object.keys(buckets) as Array<keyof typeof buckets>).map((label) => ({
    label,
    total: buckets[label],
    color: riskPalette[label]
  }));
}

function buildIncidentStateDistribution(
  states: Array<
    | "new"
    | "triaged"
    | "investigating"
    | "contained"
    | "resolved"
    | "false_positive"
    | "failed"
  >
): DashboardDistributionPoint[] {
  const normalizedStateCounts = states.reduce<Record<IncidentStateBucket, number>>(
    (counts, state) => {
      if (state === "failed") {
        counts.new += 1;
      } else {
        counts[state] += 1;
      }

      return counts;
    },
    {
      new: 0,
      triaged: 0,
      investigating: 0,
      contained: 0,
      resolved: 0,
      false_positive: 0
    }
  );

  const orderedBuckets: IncidentStateBucket[] = [
    "new",
    "triaged",
    "investigating",
    "contained",
    "resolved",
    "false_positive"
  ];

  return orderedBuckets.map((label) => ({
    label,
    total: normalizedStateCounts[label],
    color: incidentStatePalette[label]
  }));
}

function buildAlertsByDetection(
  detectionTotals: DashboardSummaryApiResponse["alerts_by_detection"]
): DashboardDetectionPoint[] {
  return detectionTotals.map((item) => ({
    detectionType: item.detection_type,
    total: item.total
  }));
}

function countRecentResponses(responseTimestamps: string[]) {
  const threshold = Date.now() - 24 * 60 * 60 * 1000;
  return responseTimestamps.filter((value) => {
    const date = new Date(value);
    return !Number.isNaN(date.getTime()) && date.getTime() >= threshold;
  }).length;
}

async function fetchDashboardOverview(): Promise<DashboardOverviewResponse> {
  const [
    summary,
    alertsResponse,
    criticalAlertsResponse,
    highAlertsResponse,
    incidentsResponse,
    assetsResponse,
    onlineAssetsResponse,
    degradedAssetsResponse,
    responsesResponse
  ] = await Promise.all([
    fetchApiJson<DashboardSummaryApiResponse>("/dashboard/summary"),
    fetchApiJson<AlertsListApiResponse>(
      buildApiPath("/alerts", {
        sort_by: "timestamp",
        sort_direction: "desc",
        page: 1,
        page_size: 100,
        date_range: "all"
      })
    ),
    fetchApiJson<AlertsListApiResponse>(
      buildApiPath("/alerts", {
        severity: "critical",
        page: 1,
        page_size: 1,
        date_range: "all"
      })
    ),
    fetchApiJson<AlertsListApiResponse>(
      buildApiPath("/alerts", {
        severity: "high",
        page: 1,
        page_size: 1,
        date_range: "all"
      })
    ),
    fetchApiJson<IncidentsListApiResponse>(
      buildApiPath("/incidents", {
        sort_by: "updated_at",
        sort_direction: "desc",
        page: 1,
        page_size: 100
      })
    ),
    fetchApiJson<AssetsListApiResponse>(
      buildApiPath("/assets", {
        sort_by: "recent_alerts",
        sort_direction: "desc",
        page: 1,
        page_size: 100
      })
    ),
    fetchApiJson<AssetsListApiResponse>(
      buildApiPath("/assets", {
        status: "online",
        page: 1,
        page_size: 1
      })
    ),
    fetchApiJson<AssetsListApiResponse>(
      buildApiPath("/assets", {
        status: "degraded",
        page: 1,
        page_size: 1
      })
    ),
    fetchApiJson<ResponsesListApiResponse>(
      buildApiPath("/responses", {
        sort_by: "executed_at",
        sort_direction: "desc",
        page: 1,
        page_size: 100
      })
    )
  ]);

  const alerts = mapAlertsListResponse(alertsResponse);
  const incidents = mapIncidentsListResponse(incidentsResponse);
  const assets = mapAssetsListResponse(assetsResponse);
  const responses = mapResponsesListResponse(responsesResponse);

  const highRiskAlerts = criticalAlertsResponse.meta.total + highAlertsResponse.meta.total;
  const activeAssets =
    onlineAssetsResponse.meta.total + degradedAssetsResponse.meta.total;
  const recentResponses = countRecentResponses(
    responsesResponse.items.map((response) => response.executed_at ?? response.created_at)
  );

  return {
    fetchedAt: formatUtcDateTime(new Date().toISOString()),
    summary: {
      totalAlerts: summary.alert_count,
      highRiskAlerts,
      openIncidents: summary.open_incident_count,
      activeAssets,
      recentResponses,
      pendingResponses: summary.pending_response_count,
      averageRiskScore: Math.round(summary.average_risk_score)
    },
    alertVolume: buildAlertVolume(alertsResponse.items.map((alert) => alert.created_at)),
    severityDistribution: buildSeverityDistribution(
      alerts.items.map((alert) => alert.severity)
    ),
    riskDistribution: buildRiskDistribution(
      alerts.items.map((alert) => alert.riskScore)
    ),
    incidentStateDistribution: buildIncidentStateDistribution(
      incidents.items.map((incident) => incident.state)
    ),
    alertsByDetection: buildAlertsByDetection(summary.alerts_by_detection),
    latestIncidents: incidents.items.slice(0, 5),
    topAffectedAssets: assets.items.slice(0, 5),
    recentResponsesFeed: responses.items.slice(0, 5)
  };
}

export function useDashboardOverview() {
  const loader = useCallback(() => fetchDashboardOverview(), []);
  return useAsyncResource(loader);
}
