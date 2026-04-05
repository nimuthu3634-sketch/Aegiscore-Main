import { useCallback } from "react";
import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { buildApiPath } from "../../lib/api/query";
import { mapAlertsListResponse } from "../../lib/api/listTransforms";
import type {
  AlertsListApiResponse,
  AlertsListQuery,
  AlertsListResponse
} from "./types";

async function listAlerts(query: AlertsListQuery): Promise<AlertsListResponse> {
  const response = await fetchApiJson<AlertsListApiResponse>(
    buildApiPath("/alerts", {
      search: query.search,
      severity: query.severity,
      status: query.status,
      detection_type: query.detectionType,
      source_type: query.sourceType,
      asset: query.asset,
      date_range: query.dateRange,
      sort_by: query.sortBy,
      sort_direction: query.sortDirection,
      page: query.page,
      page_size: query.pageSize
    })
  );
  return mapAlertsListResponse(response);
}

export function useAlertsList(query: AlertsListQuery) {
  const loader = useCallback(() => listAlerts(query), [query]);
  return useAsyncResource(loader);
}
