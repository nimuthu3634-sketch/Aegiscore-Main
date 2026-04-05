import { useCallback } from "react";
import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { buildApiPath } from "../../lib/api/query";
import { mapResponsesListResponse } from "../../lib/api/listTransforms";
import type {
  ResponsesListApiResponse,
  ResponsesListQuery,
  ResponsesListResponse
} from "./types";

async function listResponses(
  query: ResponsesListQuery
): Promise<ResponsesListResponse> {
  const response = await fetchApiJson<ResponsesListApiResponse>(
    buildApiPath("/responses", {
      search: query.search,
      action_type: query.actionType,
      mode: query.mode,
      execution_status: query.executionStatus,
      sort_by: query.sortBy,
      sort_direction: query.sortDirection,
      page: query.page,
      page_size: query.pageSize
    })
  );
  return mapResponsesListResponse(response);
}

export function useResponsesList(query: ResponsesListQuery) {
  const loader = useCallback(() => listResponses(query), [query]);
  return useAsyncResource(loader);
}
