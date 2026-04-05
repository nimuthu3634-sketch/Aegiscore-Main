import { useEffect, useState } from "react";

type AsyncResourceState<T> = {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  reload: () => void;
};

export function useAsyncResource<T>(
  loader: () => Promise<T>
): AsyncResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let active = true;

    setIsLoading(true);
    setError(null);

    void loader()
      .then((result) => {
        if (!active) {
          return;
        }

        setData(result);
        setIsLoading(false);
      })
      .catch((loadError: unknown) => {
        if (!active) {
          return;
        }

        const message =
          loadError instanceof Error
            ? loadError.message
            : "Unknown resource error";

        setError(message);
        setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [loader, reloadToken]);

  return {
    data,
    isLoading,
    error,
    reload: () => setReloadToken((current) => current + 1)
  };
}
