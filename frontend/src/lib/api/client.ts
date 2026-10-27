/** Thrown for any failed API call. `code` is a stable key the UI maps to a message. */
export class ApiError extends Error {
  constructor(
    public readonly code: string,
    public readonly status: number,
  ) {
    super(code);
    this.name = "ApiError";
  }
}

// Same origin by default (Vercel routes /api to the backend; `next dev` proxies it).
// Set NEXT_PUBLIC_API_URL only when the API is hosted on a different domain.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

interface ErrorBody {
  error?: { code?: string };
}

/** URL of an API path, for links the browser opens directly (downloads). */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}/api${path}`;
}

/**
 * Calls the backend and returns the parsed JSON body.
 * Network failures and non-2xx responses are both surfaced as {@link ApiError}.
 */
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(apiUrl(path), init);
  } catch {
    throw new ApiError("network", 0);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorBody;
    throw new ApiError(body.error?.code ?? "generic", response.status);
  }
  return (await response.json()) as T;
}
