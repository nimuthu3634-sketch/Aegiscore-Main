import type { AlertsListApiResponse, AlertsListResponse } from "../../features/alerts/types";
import type { AssetsListApiResponse, AssetsListResponse } from "../../features/assets/types";
import type { IncidentsListApiResponse, IncidentsListResponse } from "../../features/incidents/types";
import type { ResponsesListApiResponse, ResponsesListResponse } from "../../features/responses/types";
import { formatUtcDateTime } from "../api";
import { mapListQueryMeta } from "./query";

function toAssetCriticality(
  value: AssetsListApiResponse["items"][number]["criticality"]
): AssetsListResponse["items"][number]["criticality"] {
  switch (value) {
    case "critical":
      return "mission_critical";
    case "high":
      return "high";
    case "low":
      return "low";
    default:
      return "standard";
  }
}

export function mapAlertsListResponse(
  payload: AlertsListApiResponse
): AlertsListResponse {
  return {
    items: payload.items.map((alert) => ({
      id: alert.id,
      detectionType: alert.detection_type,
      sourceType: alert.source_type,
      severity: alert.severity_label,
      status: alert.status_label === "contained" ? "investigating" : alert.status_label,
      asset: alert.asset_name ?? "Unassigned asset",
      sourceIp: alert.source_ip ?? "n/a",
      destinationPort:
        alert.destination_port != null ? String(alert.destination_port) : null,
      timestamp: formatUtcDateTime(alert.created_at),
      riskScore: alert.risk_score_value,
      username: alert.username ?? "n/a",
      eventId: alert.event_id ?? "n/a"
    })),
    total: payload.meta.total,
    generatedAt: new Date().toISOString(),
    meta: mapListQueryMeta(payload.meta)
  };
}

export function mapIncidentsListResponse(
  payload: IncidentsListApiResponse
): IncidentsListResponse {
  return {
    items: payload.items.map((incident) => ({
      id: incident.id,
      title: incident.title,
      priority: incident.priority,
      state: incident.state_label === "contained" ? "investigating" : incident.state_label,
      detectionType: incident.detection_type,
      linkedAlertsCount: incident.linked_alerts_count,
      primaryAsset: incident.primary_asset_name ?? "Unassigned asset",
      assignee: incident.assignee_name ?? "SOC Queue",
      lastUpdated: formatUtcDateTime(incident.updated_at),
      sourceType: incident.source_type,
      summary: incident.summary ?? "No incident summary available."
    })),
    total: payload.meta.total,
    generatedAt: new Date().toISOString(),
    meta: mapListQueryMeta(payload.meta)
  };
}

export function mapAssetsListResponse(
  payload: AssetsListApiResponse
): AssetsListResponse {
  return {
    items: payload.items.map((asset) => ({
      id: asset.id,
      hostname: asset.hostname,
      ipAddress: asset.ip_address,
      operatingSystem: asset.operating_system ?? "Unknown OS",
      agentStatus: asset.agent_status,
      criticality: toAssetCriticality(asset.criticality),
      recentAlertsCount: asset.recent_alerts_count,
      lastSeen: formatUtcDateTime(asset.last_seen_at),
      environment: asset.environment,
      openIncidents: asset.open_incidents_count
    })),
    total: payload.meta.total,
    generatedAt: new Date().toISOString(),
    meta: mapListQueryMeta(payload.meta)
  };
}

export function mapResponsesListResponse(
  payload: ResponsesListApiResponse
): ResponsesListResponse {
  return {
    items: payload.items.map((response) => ({
      id: response.id,
      actionType: response.action_type,
      target: response.target ?? "n/a",
      mode: response.mode ?? "live",
      linkedEntity: response.incident.id,
      executionStatus: response.execution_status_label,
      executedAt: formatUtcDateTime(response.executed_at ?? response.created_at),
      resultSummary: response.result_summary ?? "No response summary available."
    })),
    total: payload.meta.total,
    generatedAt: new Date().toISOString(),
    meta: mapListQueryMeta(payload.meta)
  };
}
