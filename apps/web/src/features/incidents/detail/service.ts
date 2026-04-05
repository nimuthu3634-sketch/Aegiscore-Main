import { useEffect, useState } from "react";
import { mockIncidentDetailsById } from "./mockData";
import type { IncidentDetailResponse } from "./types";

type IncidentDetailState = {
  data: IncidentDetailResponse | null;
  isLoading: boolean;
  error: string | null;
  notFound: boolean;
  reload: () => void;
};

async function fetchIncidentDetail(
  incidentId: string
): Promise<IncidentDetailResponse | null> {
  await new Promise((resolve) => window.setTimeout(resolve, 180));
  return mockIncidentDetailsById[incidentId] ?? null;
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
