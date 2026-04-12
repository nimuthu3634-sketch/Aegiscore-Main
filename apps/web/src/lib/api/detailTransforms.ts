import type { AnalystNote } from "../../components/data-display/AnalystNotesPanel";
import type { KeyValueItem } from "../../components/data-display/KeyValueGrid";
import type { TimelineItem } from "../../components/data-display/ActivityTimeline";
import type { RelatedResponseItem } from "../../components/data-display/RelatedResponsesPanel";
import type { AssetCriticality } from "../../features/assets/types";
import type {
  ResponseExecutionStatus,
  ResponseMode
} from "../../features/responses/types";
import { formatUtcDateTime } from "../api";
import { formatDriverLabel, formatScoreMethodLabel, formatTokenLabel } from "../formatters";

type ApiUserSummary = {
  username: string;
  full_name: string | null;
} | null;

type ApiRelatedResponse = {
  id: string;
  action_type: string;
  status: string;
  policy_name?: string | null;
  target: string | null;
  mode: string | null;
  result_summary: string | null;
  result_message?: string | null;
  attempt_count?: number | null;
  details: Record<string, unknown>;
  created_at: string;
  executed_at: string | null;
  requested_by: ApiUserSummary;
  related_notifications?: Array<{
    id: string;
    channel: string;
    delivery_mode: string;
    trigger_type: string;
    trigger_value: string;
    recipient: string;
    subject: string;
    status: string;
    error_message: string | null;
    created_at: string;
    sent_at: string | null;
  }>;
};

type ApiNote = {
  id: string;
  author: ApiUserSummary;
  content: string;
  created_at: string;
};

type ApiTimelineEntry = {
  id: string;
  timestamp: string;
  category: string;
  title: string;
  description: string | null;
  actor: ApiUserSummary;
};

function toDisplayValue(value: unknown): string {
  if (value == null) {
    return "n/a";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value.map((entry) => toDisplayValue(entry)).join(", ");
  }

  return JSON.stringify(value, null, 2);
}

function isMonospaceKey(key: string) {
  return /(ip|port|user|timestamp|time|rule|id|path|hash|ref|event|asset_hostname)/i.test(
    key
  );
}

export function toSourceType(value: string | null | undefined): "Wazuh" | "Suricata" {
  return value?.toLowerCase() === "suricata" ? "Suricata" : "Wazuh";
}

export function toActorLabel(actor: ApiUserSummary) {
  return actor?.full_name ?? actor?.username ?? "AegisCore System";
}

export function toRelatedResponses(
  responses: ApiRelatedResponse[]
): RelatedResponseItem[] {
  return responses.map((response) => ({
    id: response.id,
    actionType: response.action_type,
    policyName: response.policy_name ?? null,
    target: response.target ?? "n/a",
    mode: (response.mode === "dry-run" ? "dry-run" : "live") as ResponseMode,
    executionStatus: toResponseExecutionStatus(response.status),
    executedAt: formatUtcDateTime(response.executed_at ?? response.created_at),
    resultSummary:
      response.result_summary ??
      toDisplayValue(response.details["result"]) ??
      "No response summary available.",
    resultMessage: response.result_message ?? null,
    attemptCount: response.attempt_count ?? 0,
    requestedBy: toActorLabel(response.requested_by),
    details:
      response.details && typeof response.details === "object"
        ? (response.details as Record<string, unknown>)
        : undefined,
    relatedNotifications: (response.related_notifications ?? []).map((event) => ({
      id: event.id,
      recipient: event.recipient,
      status: event.status,
      triggerType: event.trigger_type,
      deliveryMode: event.delivery_mode,
      subject: event.subject
    }))
  }));
}

export function toAnalystNotes(notes: ApiNote[]): AnalystNote[] {
  return notes.map((note) => ({
    id: note.id,
    author: toActorLabel(note.author),
    timestamp: formatUtcDateTime(note.created_at),
    content: note.content
  }));
}

export function toTimelineItems(entries: ApiTimelineEntry[]): TimelineItem[] {
  return entries.map((entry) => ({
    id: entry.id,
    timestamp: formatUtcDateTime(entry.timestamp),
    actor: toActorLabel(entry.actor),
    title: entry.title,
    description: entry.description ?? "No additional timeline details were provided.",
    tone:
      entry.category === "response"
        ? "success"
        : entry.category === "alert"
          ? "warning"
          : "brand"
  }));
}

export function toAssetCriticality(
  criticality: string | null | undefined
): AssetCriticality {
  switch (criticality) {
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

export function toKeyValueItems(details: Record<string, unknown>): KeyValueItem[] {
  const items = Object.entries(details).map(([key, value]) => ({
    label: toLabel(key),
    value: toDisplayValue(value),
    mono: isMonospaceKey(key),
    emphasized: !isMonospaceKey(key)
  }));

  return items.length
    ? items
    : [
        {
          label: "Normalized details",
          value: "No normalized details were returned by the backend.",
          emphasized: true
        }
      ];
}

function toResponseExecutionStatus(status: string): ResponseExecutionStatus {
  switch (status) {
    case "completed":
      return "succeeded";
    case "warning":
      return "warning";
    case "failed":
      return "failed";
    case "queued":
    case "in_progress":
    default:
      return "pending";
  }
}

function toLabel(key: string) {
  return formatTokenLabel(key);
}

export { formatDriverLabel, formatScoreMethodLabel, formatTokenLabel };
