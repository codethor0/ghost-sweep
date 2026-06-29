"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

interface SessionContextValue {
  accessToken: string | null;
  setAccessToken: (token: string | null) => void;
  clearSession: () => void;
  isAuthenticated: boolean;
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessTokenState] = useState<string | null>(null);

  const setAccessToken = useCallback((token: string | null) => {
    setAccessTokenState(token);
  }, []);

  const clearSession = useCallback(() => {
    setAccessTokenState(null);
  }, []);

  const value = useMemo(
    () => ({
      accessToken,
      setAccessToken,
      clearSession,
      isAuthenticated: accessToken !== null,
    }),
    [accessToken, setAccessToken, clearSession],
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
