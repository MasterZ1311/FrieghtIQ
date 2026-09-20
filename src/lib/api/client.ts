export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    // In browser (desktop or mobile tunnel): use relative URL so Next.js proxy rewrites handle it.
    // This avoids CORS restrictions, Mixed Content blocking, and loopback resolution issues on mobile.
    return '/api/v1';
  }
  // On server (SSR / Node): use internal backend port or environment variable
  return process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
}

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${baseUrl}${cleanEndpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      cache: 'no-store',
    });

    if (!res.ok) {
      let errorData;
      try {
        errorData = await res.json();
      } catch {
        errorData = await res.text();
      }
      throw new ApiError(res.status, `API request failed with status ${res.status}`, errorData);
    }

    return (await res.json()) as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network error or server not reachable
    console.warn(`FREIGHT IQ API connection error at ${endpoint}:`, error.message);
    throw error;
  }
}
