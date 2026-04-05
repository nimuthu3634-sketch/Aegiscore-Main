import { useCallback } from "react";
import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { buildApiPath } from "../../lib/api/query";
import { mapIncidentsListResponse } from "../../lib/api/listTransforms";
import type {
  IncidentsListApiResponse,
  IncidentsListQuery,
  IncidentsListResponse
} from "./types";

async function listIncidents(
  query: IncidentsListQuery
): Promise<IncidentsListResponse> {
  const response = await fetchApiJson<IncidentsListApiResponse>(
    buildApiPath("/incidents", {
      search: query.search,
      priority: query.priority,
      state: query.state,
      detection_type: query.detectionType,
      assignee: query.assignee,
      sort_by: query.sortBy,
      sort_direction: query.sortDirection,
      page: query.page,
      page_size: query.pageSize
    })
  );
  return mapIncidentsListResponse(response);
}

export function useIncidentsList(query: IncidentsListQuery) {
  const loader = useCallback(() => listIncidents(query), [query]);
  return useAsyncResource(loader);
}
