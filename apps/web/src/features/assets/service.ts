import { useCallback } from "react";
import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { buildApiPath } from "../../lib/api/query";
import { mapAssetsListResponse } from "../../lib/api/listTransforms";
import type { AssetsListApiResponse, AssetsListQuery, AssetsListResponse } from "./types";

async function listAssets(query: AssetsListQuery): Promise<AssetsListResponse> {
  const response = await fetchApiJson<AssetsListApiResponse>(
    buildApiPath("/assets", {
      search: query.search,
      status: query.status,
      criticality: query.criticality,
      operating_system: query.operatingSystem,
      environment: query.environment,
      sort_by: query.sortBy,
      sort_direction: query.sortDirection,
      page: query.page,
      page_size: query.pageSize
    })
  );

  return mapAssetsListResponse(response);
}

export function useAssetsList(query: AssetsListQuery) {
  const loader = useCallback(() => listAssets(query), [query]);
  return useAsyncResource(loader);
}
