import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { mapAssetsListResponse } from "../../lib/api/listTransforms";
import type { AlertsListApiResponse } from "../alerts/types";
import type { IncidentsListApiResponse } from "../incidents/types";
import type { AssetsListApiResponse, AssetsListResponse } from "./types";

async function listAssets(): Promise<AssetsListResponse> {
  const [assets, alerts, incidents] = await Promise.all([
    fetchApiJson<AssetsListApiResponse>("/assets"),
    fetchApiJson<AlertsListApiResponse>("/alerts"),
    fetchApiJson<IncidentsListApiResponse>("/incidents")
  ]);

  return mapAssetsListResponse(assets, { alerts, incidents });
}

export function useAssetsList() {
  return useAsyncResource(listAssets);
}
