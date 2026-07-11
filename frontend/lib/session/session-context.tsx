"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

interface SessionContextValue {
  accessToken: string | null;
  refreshToken: string | null;
  setSessionTokens: (accessToken: string, refreshToken: string) => void;
  clearSession: () => Promise<void>;
  isAuthenticated: boolean;
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessTokenState] = useState<string | null>(null);
  const [refreshToken, setRefreshTokenState] = useState<string | null>(null);

  const setSessionTokens = useCallback((nextAccessToken: string, nextRefreshToken: string) => {
    setAccessTokenState(nextAccessToken);
    setRefreshTokenState(nextRefreshToken);
  }, []);

  const clearSession = useCallback(async () => {
    const tokenToRevoke = refreshToken;
    setAccessTokenState(null);
    setRefreshTokenState(null);
    if (!tokenToRevoke) {
      return;
    }
    try {
      const { logoutUser } = await import("@/lib/api/endpoints");
      await logoutUser(tokenToRevoke);
    } catch {
      // Local session state is already cleared even when revocation fails.
    }
  }, [refreshToken]);

  const value = useMemo(
    () => ({
      accessToken,
      refreshToken,
      setSessionTokens,
      clearSession,
      isAuthenticated: accessToken !== null,
    }),
    [accessToken, refreshToken, setSessionTokens, clearSession],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return context;
}
