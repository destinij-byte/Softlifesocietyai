import { useCallback, useState } from "react";
import { useFocusEffect } from "expo-router";
import { ApiError } from "@/services/api";

type AsyncDataState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
};

/**
 * Standardizes the load-on-focus + loading/error/retry pattern that was
 * previously hand-rolled per screen (most of which never caught a failed
 * fetch at all, leaving a blank screen and an unhandled rejection). Reloads
 * on every screen focus, same as the useFocusEffect(() => load()) pattern
 * this replaces.
 */
export function useAsyncData<T>(fetcher: () => Promise<T>): AsyncDataState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      setLoading(true);
      setError(null);
      fetcher()
        .then((result) => {
          if (!cancelled) setData(result);
        })
        .catch((err) => {
          if (!cancelled) setError(err instanceof ApiError ? err.message : "Something went wrong loading this.");
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
      return () => {
        cancelled = true;
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [reloadToken])
  );

  const refetch = useCallback(() => setReloadToken((t) => t + 1), []);

  return { data, loading, error, refetch };
}
