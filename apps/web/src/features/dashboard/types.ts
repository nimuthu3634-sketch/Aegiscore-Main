import type { AssetRecord } from "../assets/types";
import type { IncidentRecord } from "../incidents/types";
import type { ResponseRecord } from "../responses/types";

export type DashboardSummaryApiResponse = {
  asset_count: number;
  raw_alert_count: number;
  alert_count: number;
  open_incident_count: number;
  pending_response_count: number;
  average_risk_score: number;
  alerts_by_detection: Array<{
    detection_type: string;
    total: number;
  }>;
};

export type DashboardTrendPoint = {
  label: string;
  total: number;
};

export type DashboardDistributionPoint = {
  label: string;
  total: number;
  color: string;
};

export type DashboardDetectionPoint = {
  detectionType: string;
  total: number;
};

export type DashboardOverviewResponse = {
  fetchedAt: string;
  summary: {
    totalAlerts: number;
    highRiskAlerts: number;
    openIncidents: number;
    activeAssets: number;
    recentResponses: number;
    pendingResponses: number;
    averageRiskScore: number;
  };
  alertVolume: DashboardTrendPoint[];
  severityDistribution: DashboardDistributionPoint[];
  riskDistribution: DashboardDistributionPoint[];
  incidentStateDistribution: DashboardDistributionPoint[];
  alertsByDetection: DashboardDetectionPoint[];
  latestIncidents: IncidentRecord[];
  topAffectedAssets: AssetRecord[];
  recentResponsesFeed: ResponseRecord[];
};
