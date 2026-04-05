import { useEffect, useState } from "react";
import { mockAlertDetailsById } from "./mockData";
import type { AlertDetailResponse } from "./types";

type AlertDetailState = {
  data: AlertDetailResponse | null;
  isLoading: boolean;
  error: string | null;
  notFound: boolean;
  reload: () => void;
};

async function fetchAlertDetail(alertId: string): Promise<AlertDetailResponse | null> {
  await new Promise((resolve) => window.setTimeout(resolve, 160));
  return mockAlertDetailsById[alertId] ?? null;
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
