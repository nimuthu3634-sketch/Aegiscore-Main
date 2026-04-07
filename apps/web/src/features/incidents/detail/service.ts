import { useEffect, useState } from "react";
import { ApiRequestError, fetchApiJson, formatUtcDateTime } from "../../../lib/api";
import {
  formatScoreMethodLabel,
  toAnalystNotes,
  toAssetCriticality,
  toRelatedResponses,
  toSourceType,
  toTimelineItems
} from "../../../lib/api/detailTransforms";
import type {
  IncidentAnalystNoteCreateApiResponse,
  IncidentDetailApiResponse,
  IncidentDetailResponse,
  IncidentTransitionApiResponse
} from "./types";

type IncidentDetailState = {
  data: IncidentDetailResponse | null;
  isLoading: boolean;
  error: string | null;
  notFound: boolean;
  reload: () => void;
};

function countAlertsForAsset(
  hostname: string,
  linkedAlerts: IncidentDetailApiResponse["linked_alerts"]
) {
  return linkedAlerts.filter((alert) => alert.asset_hostname === hostname).length;
}

function mapIncidentDetailResponse(
  payload: IncidentDetailApiResponse
): IncidentDetailResponse {
  const primaryAssetSummary = payload.primary_asset
    ? {
        hostname: payload.primary_asset.hostname,
        ipAddress: payload.primary_asset.ip_address,
        criticality: toAssetCriticality(payload.primary_asset.criticality),
        recentAlertsCount: countAlertsForAsset(
          payload.primary_asset.hostname,
          payload.linked_alerts
        )
      }
    : {
        hostname: "Unassigned asset",
        ipAddress: "n/a",
        criticality: "low" as const,
        recentAlertsCount: payload.linked_alerts.length
      };

  const affectedAssets =
    payload.affected_assets.length > 0
      ? payload.affected_assets.map((asset) => ({
          hostname: asset.hostname,
          ipAddress: asset.ip_address,
          criticality: toAssetCriticality(asset.criticality),
          recentAlertsCount: countAlertsForAsset(asset.hostname, payload.linked_alerts)
        }))
      : [primaryAssetSummary];

  return {
    fetchedAt: formatUtcDateTime(new Date().toISOString()),
    incident: {
      id: payload.id,
      title: payload.title,
      summary: payload.summary ?? "No incident summary available.",
      priority: payload.priority,
      state: payload.state,
      assignee:
        payload.assignee?.full_name ??
        payload.assignee?.username ??
        "SOC Queue",
      createdAt: formatUtcDateTime(payload.created_at),
      updatedAt: formatUtcDateTime(payload.updated_at),
      primaryAsset: payload.primary_asset?.hostname ?? "Unassigned asset",
      detectionType:
        payload.linked_alerts[0]?.detection_type ??
        String(payload.grouped_evidence.correlation_keys.detection_type ?? "unknown"),
      linkedAlertsCount: payload.linked_alerts.length,
      sourceType: toSourceType(
        payload.linked_alerts[0]?.source_type ??
          String(payload.grouped_evidence.correlation_keys.source_type ?? "Wazuh")
      ),
      linkedAlerts: payload.linked_alerts.map((alert) => ({
        id: alert.id,
        detectionType: alert.detection_type,
        sourceType: toSourceType(alert.source_type),
        severity: alert.severity,
        status: alert.status,
        asset: alert.asset_hostname ?? "Unknown asset",
        sourceIp: alert.source_ip ?? "n/a",
        timestamp: formatUtcDateTime(alert.timestamp),
        riskScore: alert.risk_score,
        eventId: null
      })),
      primaryAssetSummary,
      affectedAssets,
      timeline: toTimelineItems(payload.timeline),
      notes: toAnalystNotes(payload.analyst_notes),
      relatedResponses: toRelatedResponses(payload.response_history),
      correlationExplanation: payload.grouped_evidence.summary,
      groupedEvidence: payload.grouped_evidence.evidence_items,
      notifications: payload.notifications.map((event) => ({
        id: event.id,
        channel: event.channel,
        deliveryMode: event.delivery_mode,
        triggerType: event.trigger_type,
        triggerValue: event.trigger_value,
        recipient: event.recipient,
        subject: event.subject,
        status: event.status,
        createdAt: formatUtcDateTime(event.created_at),
        sentAt: formatUtcDateTime(event.sent_at),
        errorMessage: event.error_message
      })),
      priorityExplanation: {
        label: payload.priority_explanation.label,
        summary: payload.priority_explanation.summary,
        rationale: payload.priority_explanation.rationale,
        factors: payload.priority_explanation.factors,
        rollupScore: payload.priority_explanation.rollup_score ?? null,
        linkedAlertsCount:
          payload.priority_explanation.linked_alerts_count ?? payload.linked_alerts.length,
        scoringMethods: (payload.priority_explanation.scoring_methods ?? []).map((value) =>
          formatScoreMethodLabel(value)
        )
      },
      availableActions: payload.state_transition_capabilities.available_actions
    }
  };
}

async function fetchIncidentDetail(
  incidentId: string
): Promise<IncidentDetailResponse | null> {
  try {
    const response = await fetchApiJson<IncidentDetailApiResponse>(
      `/incidents/${incidentId}`
    );
    return mapIncidentDetailResponse(response);
  } catch (error: unknown) {
    if (error instanceof ApiRequestError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export async function transitionIncident(
  incidentId: string,
  action: "triage" | "investigate" | "contain" | "resolve" | "mark_false_positive"
) {
  return fetchApiJson<IncidentTransitionApiResponse>(`/incidents/${incidentId}/transition`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ action })
  });
}

export async function saveIncidentNote(incidentId: string, content: string) {
  return fetchApiJson<IncidentAnalystNoteCreateApiResponse>(`/incidents/${incidentId}/notes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ content })
  });
}

export function useIncidentDetail(
  incidentId: string | undefined
): IncidentDetailState {
  const [data, setData] = useState<IncidentDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;

    if (!incidentId) {
      setData(null);
      setIsLoading(false);
      setError(null);
      setNotFound(true);
      return undefined;
    }

    setIsLoading(true);
    setError(null);
    setNotFound(false);

    void fetchIncidentDetail(incidentId)
      .then((response) => {
        if (!active) {
          return;
        }

        if (!response) {
          setData(null);
          setNotFound(true);
          setIsLoading(false);
          return;
        }

        setData(response);
        setIsLoading(false);
      })
      .catch((loadError: unknown) => {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unknown incident detail error"
        );
        setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [incidentId, reloadToken]);

  return {
    data,
    isLoading,
    error,
    notFound,
    reload: () => setReloadToken((value) => value + 1)
  };
}
