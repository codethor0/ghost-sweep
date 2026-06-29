const DEFAULT_PUBLIC_API_BASE_URL = "http://localhost:8000";

function isLoopbackHost(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1";
}

function resolveServerApiBaseUrl(publicBaseUrl: string): string {
  const internalBaseUrl = process.env.INTERNAL_API_BASE_URL;
  if (internalBaseUrl) {
    return internalBaseUrl;
  }

  try {
    const parsed = new URL(publicBaseUrl);
    if (isLoopbackHost(parsed.hostname)) {
      return "http://backend:8000";
    }
  } catch {
    // Fall through to public URL.
  }

  return publicBaseUrl;
}

function resolveApiBaseUrl(): string {
  const publicBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_PUBLIC_API_BASE_URL;

  if (typeof window !== "undefined") {
    return publicBaseUrl;
  }

  return resolveServerApiBaseUrl(publicBaseUrl);
}

export const API_BASE_URL = resolveApiBaseUrl();

export const API_PREFIX = "/api/v1";
