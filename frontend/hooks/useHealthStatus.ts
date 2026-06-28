"use client";

import { useEffect, useState } from "react";

import { fetchHealthStatus, type HealthStatus } from "@/lib/api";

export function useHealthStatus(): {
  health: HealthStatus | null;
  error: string | null;
  loading: boolean;
} {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    fetchHealthStatus()
      .then((result) => {
        if (active) {
          setHealth(result);
        }
      })
      .catch((fetchError: Error) => {
        if (active) {
          setError(fetchError.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return { health, error, loading };
}
