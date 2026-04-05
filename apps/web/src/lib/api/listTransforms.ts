import type { AlertsListApiResponse, AlertsListResponse } from "../../features/alerts/types";
import type { AssetAgentStatus, AssetsListApiResponse, AssetsListResponse } from "../../features/assets/types";
import type { IncidentsListApiResponse, IncidentsListResponse } from "../../features/incidents/types";
import type {
  ResponseExecutionStatus,
  ResponseMode,
  ResponsesListApiResponse,
  ResponsesListResponse
} from "../../features/responses/types";
import type { Severity, StatusTone } from "../theme/tokens";
import { formatUtcDateTime } from "../api";

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as JsonRecord;
  }

  return null;
}

function toDisplayString(value: unknown): string | null {
  if (value == null) {
    return null;
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    const entries = value
      .map((entry) => toDisplayString(entry))
      .filter((entry): entry is string => Boolean(entry));

    return entries.length ? entries.join(", ") : null;
  }

  return null;
}

function humanizeToken(value: string) {
  return value.replace(/[_-]+/g, " ");
}

function extractPayloadValue(
  payloads: Array<JsonRecord | null | undefined>,
  keys: string[]
): unknown {
  for (const payload of payloads) {
    if (!payload) {
      continue;
    }

    for (const key of keys) {
      const value = payload[key];
      if (value != null) {
        return value;
      }
    }
  }

  return null;
}

function toSourceType(value: string | null | undefined): "Wazuh" | "Suricata" {
  return value?.toLowerCase() === "suricata" ? "Suricata" : "Wazuh";
}

function toSeverity(value: number): Severity {
  if (value >= 9) {
    return "critical";
  }

  if (value >= 7) {
    return "high";
  }

  if (value >= 4) {
    return "medium";
  }

  return "low";
}

function toAlertStatus(
  value: AlertsListApiResponse["items"][number]["status"],
  hasLinkedIncident: boolean
): StatusTone {
  if (value === "resolved") {
    return "resolved";
  }

  if (value === "investigating") {
    return "investigating";
  }

  return hasLinkedIncident ? "triaged" : "new";
}

function toIncidentState(
  value: IncidentsListApiResponse["items"][number]["status"],
  hasAssignee: boolean
): IncidentsListResponse["items"][number]["state"] {
  if (value === "resolved") {
    return "resolved";
  }

  if (value === "investigating") {
    return "investigating";
  }

  return hasAssignee ? "triaged" : "new";
}

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

function toAgentStatus(updatedAt: string): AssetAgentStatus {
  const updatedTime = new Date(updatedAt).getTime();
  if (Number.isNaN(updatedTime)) {
    return "degraded";
  }

  const ageMs = Date.now() - updatedTime;
  if (ageMs <= 30 * 60 * 1000) {
    return "online";
  }

  if (ageMs <= 2 * 60 * 60 * 1000) {
    return "degraded";
  }

  return "offline";
}

function toEnvironment(
  hostname: string
): AssetsListResponse["items"][number]["environment"] {
  if (/branch|office/i.test(hostname)) {
    return "office";
  }

  if (/edge|warehouse|vpn|remote/i.test(hostname)) {
    return "remote";
  }

  return "production";
}

function toResponseMode(details: JsonRecord): ResponseMode {
  const value = extractPayloadValue(
    [details],
    ["mode", "run_mode", "execution_mode"]
  );

  return value === "dry-run" || value === "dry_run" ? "dry-run" : "live";
}

function toResponseExecutionStatus(
  value: ResponsesListApiResponse["items"][number]["status"]
): ResponseExecutionStatus {
  switch (value) {
    case "completed":
      return "succeeded";
    case "failed":
      return "failed";
    case "queued":
    case "in_progress":
    default:
      return "pending";
  }
}

function countAlertsByAssetId(alerts: AlertsListApiResponse["items"]) {
  const counts = new Map<string, number>();

  for (const alert of alerts) {
    const assetId = alert.asset?.id;
    if (!assetId) {
      continue;
    }

    counts.set(assetId, (counts.get(assetId) ?? 0) + 1);
  }

  return counts;
}

function countOpenIncidentsByAssetId(incidents: IncidentsListApiResponse["items"]) {
  const counts = new Map<string, number>();

  for (const incident of incidents) {
    if (incident.status === "resolved") {
      continue;
    }

    const assetId = incident.alert.asset?.id;
    if (!assetId) {
      continue;
    }

    counts.set(assetId, (counts.get(assetId) ?? 0) + 1);
  }

  return counts;
}

function toResponseSummary(
  details: JsonRecord,
  status: ResponsesListApiResponse["items"][number]["status"]
) {
  const summary = toDisplayString(
    extractPayloadValue([details], [
      "result_summary",
      "summary",
      "message",
      "reason"
    ])
  );

  if (summary) {
    return summary;
  }

  const result = toDisplayString(extractPayloadValue([details], ["result"]));
  if (result) {
    return humanizeToken(result);
  }

  return humanizeToken(status);
}

function toResponseTarget(
  details: JsonRecord,
  incidentTitle: string
) {
  return (
    toDisplayString(
      extractPayloadValue([details], [
        "target",
        "username",
        "path",
        "ip_address",
        "hostname",
        "asset_hostname",
        "file_path"
      ])
    ) ?? incidentTitle
  );
}

function extractAlertSourceIp(alert: AlertsListApiResponse["items"][number]) {
  return (
    toDisplayString(
      extractPayloadValue([alert.normalized_payload, alert.raw_alert.raw_payload], [
        "source_ip",
        "src_ip",
        "sourceIp",
        "scanner_ip"
      ])
    ) ?? alert.asset?.ip_address ?? "n/a"
  );
}

function extractAlertDestinationPort(alert: AlertsListApiResponse["items"][number]) {
  return toDisplayString(
    extractPayloadValue([alert.normalized_payload, alert.raw_alert.raw_payload], [
      "destination_port",
      "dest_port",
      "dst_port",
      "destinationPort",
      "target_ports",
      "port"
    ])
  );
}

function extractAlertUsername(alert: AlertsListApiResponse["items"][number]) {
  return (
    toDisplayString(
      extractPayloadValue([alert.normalized_payload, alert.raw_alert.raw_payload], [
        "username",
        "new_user",
        "user",
        "account_name"
      ])
    ) ?? "n/a"
  );
}

function extractAlertAssetName(alert: AlertsListApiResponse["items"][number]) {
  return (
    alert.asset?.hostname ??
    toDisplayString(
      extractPayloadValue([alert.normalized_payload, alert.raw_alert.raw_payload], [
        "asset_hostname",
        "target_hostname",
        "agent"
      ])
    ) ??
    "Unassigned asset"
  );
}

export function mapAlertsListResponse(
  payload: AlertsListApiResponse
): AlertsListResponse {
  return {
    items: payload.items.map((alert) => ({
      id: alert.id,
      detectionType: alert.detection_type,
      sourceType: toSourceType(alert.source),
      severity: toSeverity(alert.severity),
      status: toAlertStatus(alert.status, Boolean(alert.incident)),
      asset: extractAlertAssetName(alert),
      sourceIp: extractAlertSourceIp(alert),
      destinationPort: extractAlertDestinationPort(alert),
      timestamp: formatUtcDateTime(alert.created_at),
      riskScore: alert.risk_score ? Math.round(alert.risk_score.score * 100) : null,
      username: extractAlertUsername(alert),
      eventId: alert.raw_alert.external_id ?? alert.raw_alert.id
    })),
    total: payload.items.length,
    generatedAt: new Date().toISOString()
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
      state: toIncidentState(incident.status, Boolean(incident.assigned_user)),
      detectionType: incident.alert.detection_type,
      linkedAlertsCount: 1,
      primaryAsset:
        incident.alert.asset?.hostname ??
        toDisplayString(incident.alert.normalized_payload["asset_hostname"]) ??
        "Unassigned asset",
      assignee:
        incident.assigned_user?.full_name ??
        incident.assigned_user?.username ??
        "SOC Queue",
      lastUpdated: formatUtcDateTime(incident.updated_at),
      sourceType: toSourceType(incident.alert.source),
      summary:
        incident.summary ??
        incident.alert.description ??
        incident.alert.title
    })),
    total: payload.items.length,
    generatedAt: new Date().toISOString()
  };
}

type AssetListContext = {
  alerts: AlertsListApiResponse;
  incidents: IncidentsListApiResponse;
};

export function mapAssetsListResponse(
  payload: AssetsListApiResponse,
  context?: AssetListContext
): AssetsListResponse {
  const alertCounts = context ? countAlertsByAssetId(context.alerts.items) : new Map();
  const openIncidentCounts = context
    ? countOpenIncidentsByAssetId(context.incidents.items)
    : new Map();

  return {
    items: payload.items.map((asset) => ({
      id: asset.id,
      hostname: asset.hostname,
      ipAddress: asset.ip_address,
      operatingSystem: asset.operating_system ?? "Unknown OS",
      agentStatus: toAgentStatus(asset.updated_at),
      criticality: toAssetCriticality(asset.criticality),
      recentAlertsCount: alertCounts.get(asset.id) ?? 0,
      lastSeen: formatUtcDateTime(asset.updated_at),
      environment: toEnvironment(asset.hostname),
      openIncidents: openIncidentCounts.get(asset.id) ?? 0
    })),
    total: payload.items.length,
    generatedAt: new Date().toISOString()
  };
}

export function mapResponsesListResponse(
  payload: ResponsesListApiResponse
): ResponsesListResponse {
  return {
    items: payload.items.map((response) => {
      const details = asRecord(response.details) ?? {};

      return {
        id: response.id,
        actionType: response.action_type,
        target: toResponseTarget(details, response.incident.title),
        mode: toResponseMode(details),
        linkedEntity: response.incident.id,
        executionStatus: toResponseExecutionStatus(response.status),
        executedAt: formatUtcDateTime(response.executed_at ?? response.created_at),
        resultSummary: toResponseSummary(details, response.status)
      };
    }),
    total: payload.items.length,
    generatedAt: new Date().toISOString()
  };
}
