const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface HealthStatus {
  status: string;
  service: string;
}

export async function fetchHealthStatus(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    next: { revalidate: 30 },
  });

  if (!response.ok) {
    throw new Error("Unable to load service health");
  }

  return response.json() as Promise<HealthStatus>;
}
