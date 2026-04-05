import { useEffect, useState } from "react";
import { ApiRequestError, fetchApiJson, formatUtcDateTime } from "../../../lib/api";
import {
  formatDriverLabel,
  formatScoreMethodLabel,
  toActorLabel,
  toAnalystNotes,
  toKeyValueItems,
  toRelatedResponses,
  toSourceType
} from "../../../lib/api/detailTransforms";
import type {
  AlertDetailApiResponse,
  AlertDetailResponse,
  AlertLifecycleApiResponse,
  AlertLinkIncidentApiRequest,
  AlertLinkIncidentApiResponse,
  AnalystNoteCreateApiResponse
} from "./types";

type AlertDetailState = {
  data: AlertDetailResponse | null;
  isLoading: boolean;
  error: string | null;
  notFound: boolean;
  reload: () => void;
};

function mapAlertDetailResponse(payload: AlertDetailApiResponse): AlertDetailResponse {
  return {
    fetchedAt: formatUtcDateTime(new Date().toISOString()),
    alert: {
      id: payload.id,
      title: payload.title,
      detectionType: payload.detection_type,
      sourceType: toSourceType(payload.source_type),
      severity: payload.severity,
      status: payload.status_label ?? payload.status,
      riskScore: payload.risk_score,
      priorityLabel: payload.priority_label,
      linkedIncidentId: payload.linked_incident?.id ?? null,
      linkedIncidentTitle: payload.linked_incident?.title ?? null,
      asset: payload.asset?.hostname ?? "Unassigned asset",
      sourceIp: payload.source_ip,
      destinationIp: payload.destination_ip,
      destinationPort:
        payload.destination_port != null ? String(payload.destination_port) : null,
      username: payload.username,
      timestamp: formatUtcDateTime(payload.timestamp),
      ruleId: payload.source_rule?.rule_id ?? null,
      sourceRule:
        payload.source_rule?.name ??
        payload.source_rule?.provider ??
        null,
      normalizedSummary:
        payload.description ??
        payload.score_explanation?.summary ??
        payload.title,
      normalizedDetails: toKeyValueItems(payload.normalized_details),
      rawPayload: payload.raw_payload,
      scoreExplanation: payload.score_explanation
        ? {
            score: payload.risk_score,
            label: payload.score_explanation.label,
            summary: payload.score_explanation.summary,
            rationale: payload.score_explanation.rationale,
            factors: payload.score_explanation.factors,
            drivers: (payload.score_explanation.drivers ?? [])
              .slice(0, 3)
              .map((driver) => formatDriverLabel(driver)),
            scoringMethod: formatScoreMethodLabel(payload.score_explanation.scoring_method),
            version:
              payload.score_explanation.model_version ??
              payload.score_explanation.baseline_version ??
              null,
            confidence: payload.score_explanation.confidence
          }
        : null,
      relatedResponses: toRelatedResponses(payload.related_responses),
      notes: toAnalystNotes(payload.analyst_notes),
      auditHistory: payload.audit_history.map((entry) => ({
        id: entry.id,
        timestamp: formatUtcDateTime(entry.timestamp),
        category: entry.category,
        title: entry.title,
        description: entry.description,
        actor: toActorLabel(entry.actor)
      }))
    }
  };
}

async function fetchAlertDetail(alertId: string): Promise<AlertDetailResponse | null> {
  try {
    const response = await fetchApiJson<AlertDetailApiResponse>(`/alerts/${alertId}`);
    return mapAlertDetailResponse(response);
  } catch (error: unknown) {
    if (error instanceof ApiRequestError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export async function acknowledgeAlertDetail(alertId: string) {
  return fetchApiJson<AlertLifecycleApiResponse>(`/alerts/${alertId}/acknowledge`, {
    method: "POST"
  });
}

export async function closeAlertDetail(alertId: string) {
  return fetchApiJson<AlertLifecycleApiResponse>(`/alerts/${alertId}/close`, {
    method: "POST"
  });
}

export async function linkAlertToIncident(
  alertId: string,
  request: AlertLinkIncidentApiRequest = { create_new: true }
) {
  return fetchApiJson<AlertLinkIncidentApiResponse>(`/alerts/${alertId}/link-incident`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      incident_id: request.incident_id,
      create_new: request.create_new ?? !request.incident_id,
      title: request.title,
      summary: request.summary
    })
  });
}

export async function saveAlertNote(alertId: string, content: string) {
  return fetchApiJson<AnalystNoteCreateApiResponse>(`/alerts/${alertId}/notes`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ content })
  });
}

export function useAlertDetail(alertId: string | undefined): AlertDetailState {
  const [data, setData] = useState<AlertDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;

    if (!alertId) {
      setData(null);
      setIsLoading(false);
      setError(null);
      setNotFound(true);
      return undefined;
    }

    setIsLoading(true);
    setError(null);
    setNotFound(false);

    void fetchAlertDetail(alertId)
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
          loadError instanceof Error ? loadError.message : "Unknown alert detail error"
        );
        setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [alertId, reloadToken]);

  return {
    data,
    isLoading,
    error,
    notFound,
    reload: () => setReloadToken((value) => value + 1)
  };
}
