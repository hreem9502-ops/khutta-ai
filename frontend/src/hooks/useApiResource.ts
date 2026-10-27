import { useEffect, useState } from "react";

interface Result<T> {
  key: string | null;
  data?: T;
  error?: unknown;
}

/**
 * Loads a resource when `key` changes. Pass `null` to skip loading.
 * `load` must be stable (module function or `useCallback`) for the effect to behave.
 */
export function useApiResource<T>(load: () => Promise<T>, key: string | null) {
  const [result, setResult] = useState<Result<T>>({ key: null });

  useEffect(() => {
    if (key === null) return;
    let cancelled = false;
    load().then(
      (data) => {
        if (!cancelled) setResult({ key, data });
      },
      (error: unknown) => {
        if (!cancelled) setResult({ key, error });
      },
    );
    return () => {
      cancelled = true;
    };
  }, [load, key]);

  const current = result.key === key;
  return {
    data: current ? result.data : undefined,
    error: current ? result.error : undefined,
    loading: key !== null && !current,
  };
}
