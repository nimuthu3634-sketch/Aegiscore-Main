import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { mockAssetsResponse } from "./mockData";
import type { AssetsListResponse } from "./types";

async function listAssets(): Promise<AssetsListResponse> {
  await new Promise((resolve) => window.setTimeout(resolve, 160));
  return mockAssetsResponse;
}

export function useAssetsList() {
  return useAsyncResource(listAssets);
}
